from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from models import User, Project, db  # Import the db object
from utils import parse_c_functions, create_call_graph, highlight_code  # Import utility functions
import json
import re

def setup_routes(app):
    # Registration Route
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

    # Login Route
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            user = User.query.filter_by(username=username, password=password).first()
            if user:
                session["user_id"] = user.id
                flash("Login successful!", "success")
                return redirect(url_for("projects"))  # Redirect to projects page
            else:
                flash("Invalid credentials!", "error")
        return render_template("login.html")

    # Logout Route
    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    # Index Route (Redirect to Projects or Login)
    @app.route("/")
    def index():
        user_id = session.get("user_id")
        if user_id:
            return redirect(url_for("projects"))
        return redirect(url_for("login"))

    # Projects Route
    @app.route("/projects")
    def projects():
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("login"))

        user = User.query.get(user_id)
        if user is None:
            flash("User not found. Please log in again.", "error")
            return redirect(url_for("login"))

        if not user.projects:
            flash("You don't have any projects yet. Create a new one!", "info")
        return render_template("projects.html", projects=user.projects)

    # New Project Route
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
                    window_state="[]",  # Initial window state
                    owner=user
                )
                db.session.add(new_project)
                db.session.commit()
                return redirect(url_for("project", project_id=new_project.id))
        return render_template("new_project.html")

    # Get Function Code Route
    @app.route("/get_function/<int:project_id>/<function_name>")
    def get_function(project_id, function_name):
        project = Project.query.get_or_404(project_id)
        func_dict = create_call_graph(parse_c_functions(project.file_content))
        function_data = func_dict.get(function_name, {})
        highlighted_code, style = highlight_code(function_data.get("code", ""))
        return jsonify({"code": highlighted_code, "style": style})

    # Delete Project Route
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

    # Load Windows State Route
    @app.route("/load_windows/<int:project_id>")
    def load_windows(project_id):
        project = Project.query.get_or_404(project_id)

        # Check if there is saved window state
        if not project.window_state:
            return jsonify([])  # If no state, return empty list

        # Deserialize JSON string
        code = json.loads(project.window_state)

        # Process each code block
        for data in code:
            tmp = data['code'].split("\n")
            code_str = '\n'.join(tmp[(len(tmp) - 1) // 2:])  # Only take the second half of lines
            data['code'] = code_str

            # Call syntax highlighting function
            highlighted_code, style = highlight_code(code_str)
            data['highlighted_code'] = highlighted_code
            data['style'] = style

        return jsonify(code)

    # Save Windows State Route
    @app.route("/save_windows/<int:project_id>", methods=["POST"])
    def save_windows(project_id):
        project = Project.query.get_or_404(project_id)
        window_state = request.json
        project.window_state = json.dumps(window_state)
        db.session.commit()
        return "", 200

    @app.route("/function/<int:project_id>/<function_name>")
    def view_function(project_id, function_name):
        project = Project.query.get_or_404(project_id)
        func_dict = create_call_graph(parse_c_functions(project.file_content))
        function_data = func_dict.get(function_name, {})
        highlighted_code, style = highlight_code(function_data.get("code", ""))

        return render_template(
            "function_viewer.html",
            project=project,
            highlighted_code=highlighted_code,
            style=style,
        )
    @app.route("/rename_function/<int:project_id>/<old_name>", methods=["POST"])
    def rename_function(project_id, old_name):
        data = request.json
        new_name = data.get("newName")
        if not new_name:
            return jsonify({"success": False, "error": "New name is required"}), 400

        project = Project.query.get_or_404(project_id)

        # Получаем текущий код проекта
        file_content = project.file_content

        # Паттерн для поиска функции (учитывает return type, имя, параметры и тело)
        function_pattern = re.compile(
            r"(?P<return_type>\w+)\s+"  # Return type
            r"(?P<function_name>" + re.escape(old_name) + r")\s*"  # Function name (escaped old name)
            r"\((?P<parameters>[^)]*)\)\s*"  # Parameters
            r"\{(?P<function_body>(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}"  # Function body
        )

        # Ищем все совпадения паттерна в коде
        matches = function_pattern.finditer(file_content)

        # Если функция найдена, заменяем её имя во всех вхождениях
        for match in matches:
            return_type = match.group("return_type")
            parameters = match.group("parameters")
            function_body = match.group("function_body")

            # Создаем новую строку функции с новым именем
            new_function_string = f"{return_type} {new_name}({parameters}) {{{function_body}}}"

            # Заменяем старую функцию новой функцией в file_content
            file_content = file_content.replace(match.group(0), new_function_string)

        # Обновляем имя функции в вызовах (если необходимо)
        file_content = file_content.replace(f"{old_name}(", f"{new_name}(")

        # Обновляем file_content проекта
        project.file_content = file_content

        db.session.commit()

        return jsonify({"success": True})
    
    @app.route("/save_node_positions/<int:project_id>", methods=["POST"])
    def save_node_positions(project_id):
        project = Project.query.get_or_404(project_id)
        node_positions = request.json
        project.node_positions = json.dumps(node_positions)
        db.session.commit()
        return jsonify({"success": True})

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

        # Load Node Positions from DB
        node_positions = project.node_positions
        if node_positions:
            node_positions = json.loads(node_positions)
        else:
            node_positions = {}

        return render_template(
            "project.html",
            project=project,
            nodes=nodes,
            edges=edges,
            func_dict=func_dict,
            node_positions=node_positions  # Pass node positions to template
        )