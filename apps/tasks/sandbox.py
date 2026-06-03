import base64
import json
import math
import random
import sys
from dataclasses import dataclass

import numpy as np
from django.conf import settings

from apps.simulator.services import (
    WHITELISTED_MODULES,
    TimeLimitException,
    create_tracer,
    get_safe_builtins,
    is_safe_code,
)


@dataclass
class SandboxOutcome:
    completed: bool
    is_correct: bool = False
    error_message: str | None = None


class SandboxUnavailableError(Exception):
    pass


def evaluate_code_submission(user_code, task):
    is_safe, security_message = is_safe_code(user_code)
    if not is_safe:
        return SandboxOutcome(completed=False, error_message=security_message)

    executor = settings.SANDBOX_EXECUTOR
    if executor == 'docker':
        try:
            return _run_in_docker(user_code, task)
        except SandboxUnavailableError as exc:
            if not settings.SANDBOX_ALLOW_INPROCESS_FALLBACK:
                return SandboxOutcome(completed=False, error_message=str(exc))

    return _run_in_process(user_code, task)


def _run_in_process(user_code, task):
    safe_builtins = get_safe_builtins()
    execution_context = {
        '__builtins__': safe_builtins,
        'np': np,
        'math': math,
        'random': random,
    }

    try:
        sys.settrace(create_tracer(max_instructions=settings.SANDBOX_MAX_INSTRUCTIONS))
        try:
            exec(user_code, execution_context)
        finally:
            sys.settrace(None)
    except TimeLimitException as exc:
        return SandboxOutcome(completed=False, error_message=str(exc))
    except Exception as exc:
        return SandboxOutcome(completed=False, error_message=f'Syntax/Runtime Error: {exc}')

    if task.function_name not in execution_context:
        return SandboxOutcome(
            completed=False,
            error_message=f'Function {task.function_name} was not found.',
        )

    user_func = execution_context[task.function_name]

    return _evaluate_test_cases(user_func, task.test_input, task.expected_output)


def _run_in_docker(user_code, task):
    try:
        import docker
        from docker.errors import APIError, DockerException, ImageNotFound
    except ImportError as exc:
        raise SandboxUnavailableError(
            "Container sandbox is unavailable: Python package 'docker' is not installed."
        ) from exc

    payload = {
        'code': user_code,
        'function_name': task.function_name,
        'test_input': task.test_input,
        'expected_output': task.expected_output,
        'max_instructions': settings.SANDBOX_MAX_INSTRUCTIONS,
        'comparison_atol': settings.SANDBOX_COMPARISON_ATOL,
        'allowed_modules': sorted(WHITELISTED_MODULES),
    }

    try:
        client = docker.from_env()
    except Exception as exc:
        raise SandboxUnavailableError(
            f'Failed to connect to Docker daemon: {exc}'
        ) from exc

    container = None
    try:
        encoded_payload = base64.b64encode(
            json.dumps(payload, ensure_ascii=False).encode('utf-8')
        ).decode('ascii')

        container = client.containers.run(
            image=settings.SANDBOX_IMAGE,
            detach=True,
            remove=False,
            network_disabled=settings.SANDBOX_DISABLE_NETWORK,
            mem_limit=settings.SANDBOX_MEMORY_LIMIT,
            nano_cpus=int(settings.SANDBOX_CPU_LIMIT * 1_000_000_000),
            pids_limit=settings.SANDBOX_PIDS_LIMIT,
            security_opt=['no-new-privileges'],
            cap_drop=['ALL'],
            read_only=True,
            tmpfs={'/tmp': 'rw,noexec,nosuid,size=64m'},
            environment={'SANDBOX_PAYLOAD_B64': encoded_payload},
            user='sandbox',
            working_dir='/workspace',
        )

        try:
            container.wait(timeout=settings.SANDBOX_TIMEOUT_SECONDS + 1)
        except Exception:
            try:
                container.kill()
            except Exception:
                pass
            return SandboxOutcome(
                completed=False,
                error_message='Time Limit Exceeded: container execution timed out.',
            )

        stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace').strip()
        stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace').strip()
    except ImageNotFound as exc:
        raise SandboxUnavailableError(
            f"Sandbox image '{settings.SANDBOX_IMAGE}' was not found. Build it first."
        ) from exc
    except (APIError, DockerException, OSError) as exc:
        raise SandboxUnavailableError(
            f'Container sandbox error: {exc}'
        ) from exc
    finally:
        if container is not None:
            try:
                container.remove(force=True)
            except Exception:
                pass

    outcome = _parse_container_output(stdout)
    if outcome is not None:
        return outcome

    error_message = stderr or stdout or 'Sandbox container finished without a valid response.'
    return SandboxOutcome(completed=False, error_message=error_message)


def _parse_container_output(output):
    if not output:
        return None

    for line in reversed(output.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        return SandboxOutcome(
            completed=bool(payload.get('completed')),
            is_correct=bool(payload.get('correct')),
            error_message=payload.get('error'),
        )
    return None


def _call_user_function(user_func, test_input):
    if isinstance(test_input, dict):
        return user_func(**test_input)
    if isinstance(test_input, list):
        try:
            return user_func(*test_input)
        except TypeError:
            return user_func(test_input)
    return user_func(test_input)


def _get_test_cases(test_input, expected_output):
    if isinstance(test_input, dict) and isinstance(test_input.get('cases'), list):
        return [
            {
                'name': case.get('name') or f'case #{index + 1}',
                'input': case.get('input'),
                'expected': case.get('expected'),
            }
            for index, case in enumerate(test_input['cases'])
        ]

    return [{'name': 'case #1', 'input': test_input, 'expected': expected_output}]


def _evaluate_test_cases(user_func, test_input, expected_output):
    cases = _get_test_cases(test_input, expected_output)
    for case in cases:
        try:
            sys.settrace(create_tracer(max_instructions=settings.SANDBOX_MAX_INSTRUCTIONS))
            try:
                result = _call_user_function(user_func, case['input'])
            finally:
                sys.settrace(None)
        except TimeLimitException as exc:
            return SandboxOutcome(completed=False, error_message=str(exc))
        except Exception as exc:
            return SandboxOutcome(completed=False, error_message=f"Runtime Error in {case['name']}: {exc}")

        outcome = _compare_result(result, case['expected'])
        if not outcome.is_correct:
            return SandboxOutcome(
                completed=True,
                is_correct=False,
                error_message=f"{case['name']}: {outcome.error_message}",
            )

    return SandboxOutcome(completed=True, is_correct=True)


def _compare_result(result, expected):
    if isinstance(result, np.ndarray):
        result = result.tolist()
    if isinstance(expected, np.ndarray):
        expected = expected.tolist()

    is_correct = (
        str(result) == str(expected)
        if isinstance(expected, (list, dict))
        else result == expected
    )

    if not is_correct and isinstance(expected, (list, dict)):
        try:
            is_correct = np.allclose(result, expected, atol=settings.SANDBOX_COMPARISON_ATOL)
        except Exception:
            pass

    error_message = None
    if not is_correct:
        error_message = f'Expected: {expected}, Received: {result}'

    return SandboxOutcome(completed=True, is_correct=is_correct, error_message=error_message)
