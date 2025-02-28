from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import re
import networkx as nx
from pygments import highlight
from pygments.lexers import CLexer
from pygments.formatters import HtmlFormatter

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Функция для парсинга функций из C-кода
def parse_c_functions(c_code):
    function_pattern = re.compile(
        r"(?P<return_type>\w+)\s+"  # Тип возвращаемого значения
        r"(?P<function_name>\w+)\s*"  # Имя функции
        r"\((?P<parameters>[^)]*)\)\s*"  # Параметры функции
        r"\{(?P<function_body>(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}"  # Тело функции
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

# Функция для поиска внутренних вызовов функций
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

# Создание графа вызовов
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

# Подсветка синтаксиса
def highlight_code(code):
    formatter = HtmlFormatter(linenos=True, cssclass="source")
    return highlight(code, CLexer(), formatter), formatter.get_style_defs('.source')

# Главная страница
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            with open(file_path, "r") as f:
                c_code = f.read()
            functions = parse_c_functions(c_code)
            func_dict = create_call_graph(functions)
            app.config["func_dict"] = func_dict
            nodes = list(func_dict.keys())
            edges = []
            for caller, data in func_dict.items():
                for callee in data["calls"]:
                    if callee in func_dict:  # Убедимся, что вызываемая функция существует
                        edges.append([caller, callee])
            return render_template("index.html", nodes=nodes, edges=edges)
    return render_template("index.html")

# Получение кода функции
@app.route("/get_function/<function_name>")
def get_function(function_name):
    func_dict = app.config.get("func_dict", {})
    function_data = func_dict.get(function_name, {})
    highlighted_code, style = highlight_code(function_data.get("code", ""))
    return jsonify({"code": highlighted_code, "style": style})

# Страница с детальной информацией о функции
@app.route("/function/<function_name>")
def function_page(function_name):
    func_dict = app.config.get("func_dict", {})
    function_data = func_dict.get(function_name, {})
    highlighted_code, style = highlight_code(function_data.get("code", ""))
    return render_template("function.html", function_name=function_name, code=highlighted_code, style=style)

# Список всех функций
@app.route("/functions_list")
def functions_list():
    func_dict = app.config.get("func_dict", {})
    functions = [{"name": name, "code": data["code"]} for name, data in func_dict.items()]
    return render_template("functions_list.html", functions=functions)

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)