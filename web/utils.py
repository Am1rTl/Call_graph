import re
import networkx as nx
from pygments import highlight
from pygments.lexers import CLexer
from pygments.formatters import HtmlFormatter

# Function to parse C functions from code
def parse_c_functions(c_code):
    function_pattern = re.compile(
        r"(?P<return_type>\w+)\s+"  # Return type
        r"(?P<function_name>\w+)\s*"  # Function name
        r"\((?P<parameters>[^)]*)\)\s*"  # Parameters
        r"\{(?P<function_body>(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}"  # Function body
    )
    c_code = re.sub(r"else\s+if\s*\([^)]*\)\s*\{[^}]*\}", "", c_code)
    functions = []
    matches = function_pattern.finditer(c_code)
    for match in matches:
        return_type = match.group("return_type")
        function_name = match.group("function_name")
        parameters = match.group("parameters")
        function_body = match.group("function_body")
        functions.append((return_type, function_name, parameters, function_body))
    return functions

# Function to create a call graph from functions
def create_call_graph(functions):
    func_dict = {}
    for return_type, function_name, parameters, function_body in functions:
        if function_name not in func_dict:
            func_dict[function_name] = {
                "code": f"{return_type} {function_name}({parameters}) {{\n{function_body}\n}}",
                "calls": []
            }
        func_dict[function_name]["calls"] = parse_code(function_body)
    return func_dict

# Function to parse code for internal calls
def parse_code(code):
    internal_calls = []
    code_string = code.split("\n")
    for string in code_string:
        elements = string.split(' ')
        for elem in elements:
            if elem.find("(") != -1:
                bracket_index = elem.index("(")
                if bracket_index != 0 and elem[bracket_index - 1] != ' ' and elem.split("(")[0].find("*") == -1 and elem.split("(")[0].find(")") == -1:
                    internal_calls.append(elem.split("(")[0])
    return internal_calls

# Function to highlight code
def highlight_code(code):
    formatter = HtmlFormatter(linenos=True, cssclass="source")
    return highlight(code, CLexer(), formatter), formatter.get_style_defs('.source')
