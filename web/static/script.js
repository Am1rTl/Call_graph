// Список истории модальных окон
let modalHistory = [];
let activeModal = null;

// Функция активации модального окна
function activateModal(modal) {
    if (activeModal) {
        activeModal.classList.remove('active');
    }
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
function createModal(content) {
    const modal = document.createElement('div');
    modal.className = 'modal-window';
    modal.innerHTML = `
        <div class="modal-header">
            <h3>Новое модальное окно</h3>
            <span class="close" title="Закрыть">X</span>
        </div>
        <div class="modal-content">${content}</div>
        <div class="modal-actions">
            <button class="ok-btn">OK</button>
            <button class="cancel-btn">Отмена</button>
        </div>
    `;

    // Добавляем обработчик закрытия
    modal.querySelector('.close').addEventListener('click', () => {
        closeModal(modal);
    });

    // Добавляем обработчики кнопок
    modal.querySelector('.ok-btn').addEventListener('click', () => {
        alert('OK clicked!');
        closeModal(modal);
    });

    modal.querySelector('.cancel-btn').addEventListener('click', () => {
        alert('Cancel clicked!');
        closeModal(modal);
    });

    // Добавляем окно в историю и делаем активным
    modalHistory.push(modal);
    activateModal(modal);

    // Делаем окно перетаскиваемым
    makeDraggable(modal);

    // Добавляем окно в DOM
    document.body.appendChild(modal);
}

// Пример: создание модального окна при клике на узел графа
document.querySelectorAll('.graph-node').forEach(node => {
    node.addEventListener('click', () => {
        const content = `Контент для узла: ${node.textContent}`;
        createModal(content);
    });
});