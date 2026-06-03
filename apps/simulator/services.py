import ast
import sys

# --- Security Configuration ---

WHITELISTED_MODULES = {
    'math', 'random', 'itertools', 'collections', 'heapq', 'bisect', 'copy',
    'numpy', 'scipy', 'sklearn', 'pandas', 'matplotlib' 
}

# --- Loop Protection ---

class TimeLimitException(Exception):
    pass

def create_tracer(max_instructions=200000):
    """
    Creates a trace function that counts executed lines.
    If the count exceeds max_instructions, it raises TimeLimitException.
    This prevents 'while True' loops from freezing the server.
    """
    count = 0
    def tracer(frame, event, arg):
        nonlocal count
        if event == 'line':
            count += 1
            if count > max_instructions:
                raise TimeLimitException("Time Limit Exceeded: Infinite loop detected or code is too slow.")
        return tracer
    return tracer

# --- Static Analysis ---

def is_safe_code(code_str):
    """
    Static analysis:
    1. Checks syntax.
    2. Allows only specific imports (Whitelist).
    3. Blocks dangerous functions (exec, eval, open).
    4. Blocks private attributes (_attr).
    """
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"

    for node in ast.walk(tree):
        # 1. Validate Imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_module = alias.name.split('.')[0]
                if base_module not in WHITELISTED_MODULES:
                    return False, f"Security Error: Import of '{base_module}' is forbidden. Allowed: {', '.join(sorted(WHITELISTED_MODULES))}"
        
        if isinstance(node, ast.ImportFrom):
            if node.module:
                base_module = node.module.split('.')[0]
                if base_module not in WHITELISTED_MODULES:
                    return False, f"Security Error: Import from '{base_module}' is forbidden."
        
        # 2. Ban accessing private attributes (starting with _)
        if isinstance(node, ast.Attribute) and node.attr.startswith('_'):
             return False, "Security Error: Access to private attributes (starting with _) is forbidden."
             
        # 3. Ban dangerous calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in ['exec', 'eval', 'open', 'help', 'exit', 'quit', 'compile', 'globals', 'locals', 'vars']:
                return False, f"Security Error: Function '{node.func.id}' is forbidden."

    return True, ""

# --- Execution Helpers ---

def get_safe_builtins():
    """
    Returns a dictionary of allowed built-in functions.
    Crucially, it includes __import__ to allow safe imports from the whitelist.
    """
    return {
        '__import__': __import__, # Allows 'import numpy' to work (protected by is_safe_code)
        'abs': abs, 'len': len, 'range': range, 'sum': sum, 
        'min': min, 'max': max, 'int': int, 'float': float, 'str': str, 'bool': bool,
        'list': list, 'dict': dict, 'set': set, 'tuple': tuple,
        'print': print, 'round': round, 'all': all, 'any': any, 'divmod': divmod,
        'sorted': sorted, 'zip': zip, 'map': map, 'filter': filter, 'enumerate': enumerate,
        'isinstance': isinstance, 'issubclass': issubclass,
    }