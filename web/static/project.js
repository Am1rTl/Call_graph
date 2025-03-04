// static/project.js

let modalHistory = [];
let lastActiveModal = null;
let isShiftDown = false;

// Выносим функцию copyCode в глобальную область видимости
function copyCode(button) {
    const codeElement = button.closest(".modal-window").querySelector("pre code");
    let codeText = codeElement.innerText;
    const lines = codeText.split('\n');
    const middle = (lines.length / 2) - 1;

    // Берем вторую половину строк
    let secondHalf = lines.slice(middle);

    // Удаляем два последних элемента
    secondHalf = secondHalf.slice(0, -3);

    // Объединяем строки обратно в текст
    const textToCopy = secondHalf.join('\n');

    // Копируем текст
    navigator.clipboard.writeText(textToCopy)
        .then(() => {
            alert("The code was copied!");
        })
        .catch(() => {
            alert("Failed to copy code!");
        });
}

function initProject(nodes, edges, projectId) {
    // Обработчик клика по документу для активации модальных окон
    document.body.addEventListener("click", (event) => {
        const modal = event.target.closest(".modal-window");
        if (modal) {
            activateModal(modal);
        }
    });

    // Функция активации модального окна
    function activateModal(modal) {
        if (lastActiveModal) {
            lastActiveModal.classList.remove("active");
        }
        modal.classList.add("active");
        lastActiveModal = modal;
    }

    // Загрузка состояния окон
    fetch(`/load_windows/${projectId}`)
        .then(response => response.json())
        .then(data => {
            data.forEach(windowData => createModalFromState(windowData));
        });

    const networkNodes = new vis.DataSet(nodes.map((node, index) => ({
        id: index,
        label: node,
        fixed: { x: true, y: true }
    })));

    const networkEdges = new vis.DataSet(edges.map((edge, index) => ({
        from: nodes.indexOf(edge[0]),
        to: nodes.indexOf(edge[1]),
        id: index
    })));

    const container = document.getElementById("graphCanvas");
    const data = { nodes: networkNodes, edges: networkEdges };
    const options = {
        physics: false,
        layout: { hierarchical: false },
        manipulation: {
            enabled: false,  // Disable built-in manipulation
            initiallyActive: false,
            addEdge: false,
            editNode: false,
            deleteNode: false,
            deleteEdge: false,
        }
    };

    const network = new vis.Network(container, data, options);

    if (initialNodePositions && Object.keys(initialNodePositions).length > 0) {
        // loop through the nodes and update their positions.  Also make them fixed
        networkNodes.forEach(node => {
            if (initialNodePositions[node.id]) {
                networkNodes.update({ id: node.id, x: initialNodePositions[node.id].x, y: initialNodePositions[node.id].y });
            }
        });
    }

    // Keydown event listener to detect Shift key
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Shift') {
            isShiftDown = true;
        }
    });

    // Keyup event listener to detect Shift key release
    document.addEventListener('keyup', function (event) {
        if (event.key === 'Shift') {
            isShiftDown = false;
        }
    });

    network.on("click", (params) => {
        if (!isShiftDown) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const functionName = nodes[nodeId];

                // Ищем существующее модальное окно с таким же именем функции
                const existingModal = Array.from(document.querySelectorAll(".modal-window")).find(modal => {
                    const modalTitle = modal.querySelector("h3");
                    return modalTitle && modalTitle.textContent === functionName;
                });

                if (existingModal) {
                    // Если окно уже открыто, закрываем его
                    existingModal.remove();
                    modalHistory = modalHistory.filter(modal => modal !== existingModal);
                }

                // Загружаем данные функции и создаем новое модальное окно
                fetch(`/get_function/${projectId}/${functionName}`)
                    .then(response => response.json())
                    .then(data => createModal(functionName, data.code, data.style));
            }
        }
    });

    // Enable dragging when Shift key is pressed
    network.on("dragStart", function (params) {
        if (isShiftDown && params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            networkNodes.update({ id: nodeId, fixed: false }); // Make node movable
        }
    });

    // Prevent drag end event when Shift key is not pressed
    network.on("dragEnd", function (params) {
        if (isShiftDown && params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            networkNodes.update({ id: nodeId, fixed: true }); // Fix node after dragging

            // Save node positions after dragging ends
            const positions = network.getPositions();
            saveNodePositions(positions);
        }
    });

    function saveNodePositions(positions) {
        fetch(`/save_node_positions/${projectId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(positions)
        });
    }

    function createModal(name, code, style) {
        const modal = document.createElement("div");
        modal.className = "modal-window";
        modal.innerHTML = `
            <div class="modal-header">
                <span class="close">×</span>
                <h3>${name}</h3>
            </div>
            <div class="modal-content resizable">
                <style>${style}</style>
                <pre><code class="source">${code}</code></pre>
            </div>
            <div class="modal-actions">
                <button onclick="copyCode(this)">Copy Code</button>
                <button onclick="location.href='/function/${projectId}/${name}'">Details</button>
            </div>
            <div class="resize-handle"></div>
        `;
        document.body.appendChild(modal);
        modalHistory.push(modal);
        activateModal(modal); // Активируем новое окно
        makeDraggable(modal);
        makeResizable(modal);
        addCloseListener(modal);
        saveWindowState(modal);
    }

    function createModalFromState(state) {
        const modal = document.createElement("div");
        modal.className = "modal-window";
        modal.style.left = `${state.x}px`;
        modal.style.top = `${state.y}px`;
        modal.style.width = `${state.width}px`;
        modal.style.height = `${state.height}px`;

        modal.innerHTML = `
        <div class="modal-header">
            <span class="close">×</span>
            <h3>${state.name}</h3>
        </div>
        <div class="modal-content resizable">
            <style>${state.style}</style>
            <pre><code class="language-python source">${state.highlighted_code || state.code}</code></pre>
        </div>
        <div class="modal-actions">
            <button onclick="copyCode(this)">Copy Code</button>
            <button onclick="location.href='/function/${projectId}/${state.name}'">Details</button>
        </div>
        <div class="resize-handle"></div>
    `;

        // Добавляем модальное окно в DOM
        document.body.appendChild(modal);
        modalHistory.push(modal);
        activateModal(modal); // Активируем новое окно
        makeDraggable(modal);
        makeResizable(modal);
        addCloseListener(modal);

        // Вызываем подсветку синтаксиса (если Highlight.js загружена)
        const codeBlock = modal.querySelector('code');
        if (codeBlock && typeof hljs !== 'undefined') {
            hljs.highlightElement(codeBlock);
        }
    }

    function addCloseListener(modal) {
        modal.querySelector(".close").addEventListener("click", () => {
            modal.remove();
            modalHistory.pop(); // Удаляем текущее окно из истории
            lastActiveModal = modalHistory[modalHistory.length - 1]; // Получаем предыдущее окно
            if (lastActiveModal) {
                activateModal(lastActiveModal); // Активируем предыдущее окно
            }
            saveWindowState();
        });
    }

    function makeDraggable(element) {
        const header = element.querySelector(".modal-header");
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;

        header.onmousedown = (e) => {
            activateModal(element); // Активируем окно при перетаскивании
            dragMouseDown(e);
        };

        function dragMouseDown(e) {
            e = e || window.event;
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }

        function elementDrag(e) {
            e = e || window.event;
            e.preventDefault();
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            element.style.top = (element.offsetTop - pos2) + "px";
            element.style.left = (element.offsetLeft - pos1) + "px";
            saveWindowState(element);
        }

        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }

    function makeResizable(element) {
        const resizeHandle = element.querySelector(".resize-handle");
        let startX, startY, startWidth, startHeight;

        resizeHandle.addEventListener("mousedown", (e) => {
            e.stopPropagation();
            startX = e.clientX;
            startY = e.clientY;
            startWidth = parseInt(window.getComputedStyle(element).width, 10);
            startHeight = parseInt(window.getComputedStyle(element).height, 10);

            document.addEventListener("mousemove", resize);
            document.addEventListener("mouseup", stopResize);
        });

        function resize(e) {
            element.style.width = `${startWidth + e.clientX - startX}px`;
            element.style.height = `${startHeight + e.clientY - startY}px`;
            saveWindowState(element);
        }

        function stopResize() {
            document.removeEventListener("mousemove", resize);
            document.removeEventListener("mouseup", stopResize);
        }
    }

    function saveWindowState(modal) {
        const windows = Array.from(document.querySelectorAll(".modal-window")).map(modal => {
            const rect = modal.getBoundingClientRect();
            return {
                name: modal.querySelector("h3").textContent,
                x: modal.offsetLeft,
                y: modal.offsetTop,
                width: rect.width,
                height: rect.height,
                code: modal.querySelector("pre code").innerText,
                style: modal.querySelector("style").innerText
            };
        });

        fetch(`/save_windows/${projectId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(windows)
        });
    }

    // Обработчик нажатия клавиши Esc
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && lastActiveModal) {
            lastActiveModal.remove();
            modalHistory.pop(); // Удаляем текущее окно из истории
            lastActiveModal = modalHistory[modalHistory.length - 1]; // Получаем предыдущее окно
            if (lastActiveModal) {
                activateModal(lastActiveModal); // Активируем предыдущее окно
            }
            saveWindowState();
        }
    });
}