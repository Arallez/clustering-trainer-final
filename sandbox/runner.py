import ast
import base64
import json
import math
import os
import random
import sys

import numpy as np


FORBIDDEN_CALLS = {
    'compile',
    'eval',
    'exec',
    'exit',
    'globals',
    'help',
    'locals',
    'open',
    'quit',
    'vars',
}


class TimeLimitException(Exception):
    pass


def create_tracer(max_instructions):
    count = 0

    def tracer(frame, event, arg):
        nonlocal count
        if event == 'line':
            count += 1
            if count > max_instructions:
                raise TimeLimitException('Time Limit Exceeded: instruction limit reached.')
        return tracer

    return tracer


def is_safe_code(code_str, allowed_modules):
    try:
        tree = ast.parse(code_str)
    except SyntaxError as exc:
        return False, f'Syntax Error: {exc}'

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_module = alias.name.split('.')[0]
                if base_module not in allowed_modules:
                    return False, f"Security Error: Import of '{base_module}' is forbidden."

        if isinstance(node, ast.ImportFrom) and node.module:
            base_module = node.module.split('.')[0]
            if base_module not in allowed_modules:
                return False, f"Security Error: Import from '{base_module}' is forbidden."

        if isinstance(node, ast.Attribute) and node.attr.startswith('_'):
            return False, 'Security Error: Access to private attributes is forbidden.'

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                return False, f"Security Error: Function '{node.func.id}' is forbidden."

    return True, ''


def get_safe_builtins():
    return {
        '__import__': __import__,
        'abs': abs,
        'all': all,
        'any': any,
        'bool': bool,
        'dict': dict,
        'divmod': divmod,
        'enumerate': enumerate,
        'filter': filter,
        'float': float,
        'int': int,
        'isinstance': isinstance,
        'issubclass': issubclass,
        'len': len,
        'list': list,
        'map': map,
        'max': max,
        'min': min,
        'print': print,
        'range': range,
        'round': round,
        'set': set,
        'sorted': sorted,
        'str': str,
        'sum': sum,
        'tuple': tuple,
        'zip': zip,
    }


def to_jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, dict):
        return {key: to_jsonable(val) for key, val in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    return value


def call_user_function(user_func, test_input):
    if isinstance(test_input, dict):
        return user_func(**test_input)
    if isinstance(test_input, list):
        try:
            return user_func(*test_input)
        except TypeError:
            return user_func(test_input)
    return user_func(test_input)


def get_test_cases(test_input, expected_output):
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


def compare_result(result, expected, atol):
    result = to_jsonable(result)
    expected = to_jsonable(expected)

    is_correct = (
        str(result) == str(expected)
        if isinstance(expected, (list, dict))
        else result == expected
    )

    if not is_correct and isinstance(expected, (list, dict)):
        try:
            is_correct = np.allclose(result, expected, atol=atol)
        except Exception:
            pass

    error = None
    if not is_correct:
        error = f'Expected: {expected}, Received: {result}'

    return {
        'completed': True,
        'correct': is_correct,
        'error': error,
    }


def evaluate_test_cases(user_func, test_input, expected_output, max_instructions, comparison_atol):
    for case in get_test_cases(test_input, expected_output):
        try:
            sys.settrace(create_tracer(max_instructions))
            try:
                result = call_user_function(user_func, case['input'])
            finally:
                sys.settrace(None)
        except TimeLimitException as exc:
            return {'completed': False, 'correct': False, 'error': str(exc)}
        except Exception as exc:
            return {'completed': False, 'correct': False, 'error': f"Runtime Error in {case['name']}: {exc}"}

        outcome = compare_result(result, case['expected'], comparison_atol)
        if not outcome['correct']:
            outcome['error'] = f"{case['name']}: {outcome['error']}"
            return outcome

    return {'completed': True, 'correct': True, 'error': None}


def emit(payload):
    print(json.dumps(payload, ensure_ascii=False))


def main():
    payload = None

    if len(sys.argv) == 2:
        payload_path = sys.argv[1]
        with open(payload_path, 'r', encoding='utf-8') as file_obj:
            payload = json.load(file_obj)
    else:
        encoded_payload = os.environ.get('SANDBOX_PAYLOAD_B64')
        if not encoded_payload:
            emit({'completed': False, 'correct': False, 'error': 'Missing sandbox payload.'})
            return 1
        payload = json.loads(base64.b64decode(encoded_payload).decode('utf-8'))

    code = payload['code']
    function_name = payload['function_name']
    test_input = payload['test_input']
    expected_output = payload['expected_output']
    max_instructions = int(payload['max_instructions'])
    comparison_atol = float(payload.get('comparison_atol', 0.01))
    allowed_modules = set(payload.get('allowed_modules', []))

    is_safe, security_message = is_safe_code(code, allowed_modules)
    if not is_safe:
        emit({'completed': False, 'correct': False, 'error': security_message})
        return 0

    context = {
        '__builtins__': get_safe_builtins(),
        'np': np,
        'math': math,
        'random': random,
    }

    try:
        sys.settrace(create_tracer(max_instructions))
        try:
            exec(code, context)
        finally:
            sys.settrace(None)
    except TimeLimitException as exc:
        emit({'completed': False, 'correct': False, 'error': str(exc)})
        return 0
    except Exception as exc:
        emit({'completed': False, 'correct': False, 'error': f'Syntax/Runtime Error: {exc}'})
        return 0

    if function_name not in context:
        emit({'completed': False, 'correct': False, 'error': f'Function {function_name} was not found.'})
        return 0

    emit(evaluate_test_cases(context[function_name], test_input, expected_output, max_instructions, comparison_atol))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
