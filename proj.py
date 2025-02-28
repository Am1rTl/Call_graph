import re

def parse_c_functions(c_code):
    # Регулярное выражение для поиска функций в коде на C
    function_pattern = re.compile(
        r"(?P<return_type>\w+)\s+"  # Тип возвращаемого значения
        r"(?P<function_name>\w+)\s*"  # Имя функции
        r"\((?P<parameters>[^)]*)\)\s*"  # Параметры функции
        r"\{(?P<function_body>(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}"  # Тело функции
    )

    # Удаляем все конструкции else if из кода, чтобы они не мешали
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

def create_function_array(functions):
    function_array = []
    for func in functions:
        return_type, function_name, parameters, function_body = func
        function_str = f"{return_type} {function_name}({parameters}) {{\n{function_body}\n}}"
        function_array.append(function_str)
    return function_array


def parse_code(code):
	internal_calls = []

	code_string = code.split("\n")
	for string in code_string:
		elements = string.split(' ')
		for elem in elements:
			if elem.find("(") != -1:
				bracket_index = elem.index("(")
				if bracket_index != 0:
					if elem[bracket_index - 1] != ' ' and elem.split("(")[0].find("*") == -1 and elem.split("(")[0].find(")") == -1 :
						internal_calls.append(elem.split("(")[0])

	return internal_calls

if __name__ == "__main__":
    # Чтение файла с кодом на C
    with open("tmp.c", "r") as file:
        c_code = file.read()

    # Парсинг функций
    functions = parse_c_functions(c_code)

    # Создание массива функций
    function_array = create_function_array(functions)

    # Вывод результата
    func_dict = {}

    #print("Найденные функции:")
    for i, func in enumerate(function_array, 1):
        #print(f"Функция {i}:\n{func}\n")

        tmp_func = func.split("\n")
        nornal_function_name = tmp_func[0].split(' ')[1].split("(")[0]
        if nornal_function_name not in func_dict.keys():
        	func_dict[nornal_function_name] = []
        internal_calls = parse_code(func)
        func_dict[nornal_function_name] = internal_calls

    print(func_dict)

import networkx as nx
import matplotlib.pyplot as plt

# Ваш словарь вызовов функций
call_graph = func_dict

# Создаем граф
G = nx.DiGraph()

# Добавляем узлы и рёбра в граф
for caller, callees in call_graph.items():
    for callee in callees:
        G.add_edge(caller, callee)

# Визуализация графа
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G)  # Позиционирование узлов
nx.draw(G, pos, with_labels=True, node_size=2000, node_color="skyblue", font_size=10, font_weight="bold", arrows=True)
plt.title("Граф вызовов функций")
plt.show()

# Начинаем с функции entry (если она есть)
entry_function = "__security_init_cookie"  # Замените на вашу entry-функцию
if entry_function in G:
    print(f"Начинаем обход с функции: {entry_function}")
    # Пример обхода в глубину (DFS)
    dfs_tree = nx.dfs_tree(G, source=entry_function)
    print("Результат обхода в глубину (DFS):")
    print(list(dfs_tree.edges()))
else:
    print(f"Функция {entry_function} не найдена в графе.")