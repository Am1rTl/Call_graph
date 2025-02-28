from flask import Flask, request, jsonify, render_template
import re
import networkx as nx

app = Flask(__name__)

# Функция для парсинга C-функций
def parse_c_functions(c_code):
    # Улучшенное регулярное выражение для поиска функций
    function_pattern = re.compile(
        r"(?P<return_type>[\w\*\s]+?)\s+"  # Тип возвращаемого значения (может включать * и пробелы)
        r"(?P<function_name>\w+)\s*"  # Имя функции
        r"\((?P<parameters>[^)]*)\)\s*"  # Параметры функции
        r"\{(?P<function_body>(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}"  # Тело функции
    )

    # Удаляем все комментарии и лишние символы
    c_code = re.sub(r"/\*.*?\*/", "", c_code, flags=re.DOTALL)  # Удаляем многострочные комментарии
    c_code = re.sub(r"//.*", "", c_code)  # Удаляем однострочные комментарии
    c_code = re.sub(r"else\s+if\s*\([^)]*\)\s*\{[^}]*\}", "", c_code)  # Удаляем else if

    functions = []
    matches = function_pattern.finditer(c_code)

    for match in matches:
        return_type = match.group("return_type").strip()
        function_name = match.group("function_name")
        parameters = match.group("parameters")
        function_body = match.group("function_body")
        functions.append((return_type, function_name, parameters, function_body))

    return functions

# Создание массива функций
def create_function_array(functions):
    function_array = []
    for func in functions:
        return_type, function_name, parameters, function_body = func
        function_str = f"{return_type} {function_name}({parameters}) {{\n{function_body}\n}}"
        function_array.append(function_str)
    return function_array

# Анализ внутренних вызовов функций
def parse_code(code):
    internal_calls = []

    code_string = code.split("\n")
    for string in code_string:
        elements = string.split(' ')
        for elem in elements:
            if '(' in elem and ')' in elem:
                bracket_index = elem.index('(')
                if bracket_index != 0:
                    if elem[bracket_index - 1] != ' ' and elem.split("(")[0].find("*") == -1 and elem.split("(")[0].find(")") == -1:
                        internal_calls.append(elem.split("(")[0])

    return internal_calls

# Основная функция для построения графа вызовов
@app.route('/parse', methods=['POST'])
def parse():
    if 'file' in request.files:
        file = request.files['file']
        c_code = file.read().decode('utf-8')
    else:
        return jsonify({"error": "No file provided"}), 400

    # Парсим функции
    functions = parse_c_functions(c_code)
    function_array = create_function_array(functions)
    func_dict = {}

    for func in function_array:
        tmp_func = func.split("\n")
        normal_function_name = tmp_func[0].split(' ')[1].split("(")[0]
        if normal_function_name not in func_dict.keys():
            func_dict[normal_function_name] = []
        internal_calls = parse_code(func)
        func_dict[normal_function_name] = internal_calls

    # Создаем граф вызовов
    G = nx.DiGraph()
    for caller, callees in func_dict.items():
        for callee in callees:
            G.add_edge(caller, callee)

    # Преобразуем граф в формат JSON
    nodes = [{"id": node} for node in G.nodes()]
    edges = [{"source": u, "target": v} for u, v in G.edges()]

    return jsonify({
        "nodes": nodes,
        "edges": edges
    })

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)