from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import re
import networkx as nx
from pygments import highlight
from pygments.lexers import CLexer
from pygments.formatters import HtmlFormatter
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Замените на свой секретный ключ
db = SQLAlchemy(app)

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    projects = db.relationship('Project', backref='owner', lazy=True)

# Модель проекта
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_content = db.Column(db.Text, nullable=False)
    window_state = db.Column(db.Text, nullable=True)  # JSON для состояния окон
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# Создание базы данных
with app.app_context():
    db.create_all()

# Функции для анализа кода
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

def highlight_code(code):
    formatter = HtmlFormatter(linenos=True, cssclass="source")
    return highlight(code, CLexer(), formatter), formatter.get_style_defs('.source')

# Регистрация
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "error")
            return redirect(url_for("register"))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

# Логин
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user_id"] = user.id
            flash("Login successful!", "success")
            return redirect(url_for("projects"))  # Перенаправление на страницу проектов
        else:
            flash("Invalid credentials!", "error")
    return render_template("login.html")

# Выход
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# Главная страница (редирект на проекты или логин)
@app.route("/")
def index():
    user_id = session.get("user_id")
    if user_id:
        return redirect(url_for("projects"))
    return redirect(url_for("login"))

# Список проектов
@app.route("/projects")
def projects():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = User.query.get(user_id)
    if not user.projects:
        flash("You don't have any projects yet. Create a new one!", "info")
    return render_template("projects.html", projects=user.projects)

# Создание нового проекта
@app.route("/new_project", methods=["GET", "POST"])
def new_project():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files["file"]
        description = request.form.get("description", "")
        if file:
            file_content = file.read().decode("utf-8")
            project_name = file.filename
            user = User.query.get(user_id)
            new_project = Project(
                name=project_name,
                description=description,
                file_content=file_content,
                window_state="[]",  # Начальное состояние окон
                owner=user
            )
            db.session.add(new_project)
            db.session.commit()
            return redirect(url_for("project", project_id=new_project.id))
    return render_template("new_project.html")

# Проект
@app.route("/project/<int:project_id>", methods=["GET", "POST"])
def project(project_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    project = Project.query.get_or_404(project_id)
    if project.user_id != user_id:
        return "Access denied", 403

    if request.method == "POST":
        window_state = request.form.get("window_state", "[]")
        project.window_state = window_state
        db.session.commit()

    functions = parse_c_functions(project.file_content)
    func_dict = create_call_graph(functions)
    nodes = list(func_dict.keys())
    edges = []
    for caller, data in func_dict.items():
        for callee in data["calls"]:
            if callee in func_dict:
                edges.append([caller, callee])

    return render_template(
        "project.html",
        project=project,
        nodes=nodes,
        edges=edges,
        func_dict=func_dict
    )

# Получение кода функции
@app.route("/get_function/<int:project_id>/<function_name>")
def get_function(project_id, function_name):
    project = Project.query.get_or_404(project_id)
    func_dict = create_call_graph(parse_c_functions(project.file_content))
    function_data = func_dict.get(function_name, {})
    highlighted_code, style = highlight_code(function_data.get("code", ""))
    return jsonify({"code": highlighted_code, "style": style})

@app.route("/delete_project/<int:project_id>", methods=["POST"])
def delete_project(project_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    project = Project.query.get_or_404(project_id)
    if project.user_id != user_id:
        return "Access denied", 403

    db.session.delete(project)
    db.session.commit()
    flash("Project deleted successfully!", "success")
    return redirect(url_for("projects"))

    
# Загрузка состояния окон
@app.route("/load_windows/<int:project_id>")
def load_windows(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify(json.loads(project.window_state or "[]"))

# Сохранение состояния окон
@app.route("/save_windows/<int:project_id>", methods=["POST"])
def save_windows(project_id):
    project = Project.query.get_or_404(project_id)
    window_state = request.json
    project.window_state = json.dumps(window_state)
    db.session.commit()
    return "", 200

if __name__ == "__main__":
    app.run(debug=True)