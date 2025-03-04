// Список истории модальных окон
let modalHistory = [];
let activeModal = null;
let zIndexCounter = 1000;

// Функция активации модального окна
function activateModal(modal) {
    if (activeModal) {
        activeModal.classList.remove('active');
    }

    // Увеличиваем z-index для активного окна
    modal.style.zIndex = ++zIndexCounter;

    modal.classList.add('active');
    activeModal = modal;
}

// Обработчик клика по документу
document.body.addEventListener("click", (event) => {
    const target = event.target;

    // Если кликнуто на модальное окно, активируем его
    if (target.closest('.modal-window')) {
        const modal = target.closest('.modal-window');
        activateModal(modal);
    }
});

// Функция для создания перетаскиваемого окна
function makeDraggable(element) {
    let isDragging = false;
    let offsetX, offsetY;

    const header = element.querySelector('.modal-header');

    // Начало перетаскивания
    header.addEventListener('mousedown', (e) => {
        isDragging = true;
        offsetX = e.clientX - element.offsetLeft;
        offsetY = e.clientY - element.offsetTop;

        // Активируем окно при начале перетаскивания
        activateModal(element);

        // Добавляем класс "dragging" для стилей
        element.classList.add('dragging');
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;

        const x = e.clientX - offsetX;
        const y = e.clientY - offsetY;

        element.style.left = `${x}px`;
        element.style.top = `${y}px`;
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
        element.classList.remove('dragging');
    });
}

// Функция для закрытия активного окна
function closeModal(modal) {
    modal.classList.remove('active');
    modalHistory = modalHistory.filter(m => m !== modal);

    // Активируем предыдущее окно из истории
    if (modalHistory.length > 0) {
        activateModal(modalHistory[modalHistory.length - 1]);
    } else {
        activeModal = null;
    }
}

// Обработчик нажатия клавиши Esc
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && activeModal) {
        closeModal(activeModal);
    }
});

// Создание нового модального окна
function createModal(name, code, style) {
    const modal = document.createElement("div");
    modal.className = "modal-window";

    // Устанавливаем начальные ограничения на размер окна
    const initialMaxWidth = window.innerWidth * 0.5; // 50% ширины экрана
    const initialMaxHeight = window.innerHeight * 0.75; // 75% высоты экрана

    modal.style.maxWidth = `${initialMaxWidth}px`;
    modal.style.maxHeight = `${initialMaxHeight}px`;

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
            <button onclick="location.href='/function/{{ project.id }}/${name}'">Details</button>
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
        let newWidth = startWidth + (e.clientX - startX);
        let newHeight = startHeight + (e.clientY - startY);

        // Убираем ограничения на размер после начала ресайза
        element.style.maxWidth = "none";
        element.style.maxHeight = "none";

        // Минимальные размеры окна
        const minWidth = 300;
        const minHeight = 200;

        if (newWidth < minWidth) newWidth = minWidth;
        if (newHeight < minHeight) newHeight = minHeight;

        element.style.width = `${newWidth}px`;
        element.style.height = `${newHeight}px`;
        saveWindowState(element);
    }

    function stopResize() {
        document.removeEventListener("mousemove", resize);
        document.removeEventListener("mouseup", stopResize);
    }
}

// Пример: создание модального окна при клике на узел графа
document.querySelectorAll('.graph-node').forEach(node => {
    node.addEventListener('click', () => {
        const content = `Контент для узла: ${node.textContent}`;
        createModal(content);
    });
});






