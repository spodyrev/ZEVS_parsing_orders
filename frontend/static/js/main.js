// JavaScript для Taobao Order Tracker

// Загрузка статистики при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    // Автообновление каждые 30 секунд
    setInterval(loadStats, 30000);
});

/**
 * Загружает статистику с сервера
 */
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        // Обновляем счетчики
        document.getElementById('stat-shipped').textContent = data.by_status.shipped || 0;
        document.getElementById('stat-delivered').textContent = data.by_status.delivered || 0;
        document.getElementById('stat-created').textContent = data.by_status.created || 0;
        
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
    }
}

/**
 * Запускает синхронизацию заказов
 */
async function syncOrders() {
    const button = event.target.closest('button');
    const originalHTML = button.innerHTML;
    
    // Показываем индикатор загрузки
    button.disabled = true;
    button.innerHTML = '<span class="spinner"></span> Синхронизация...';
    
    try {
        const response = await fetch('/api/sync', {
            method: 'POST'
        });
        const data = await response.json();
        
        // Показываем уведомление
        showNotification('success', data.message);
        
        // Обновляем страницу через 1 секунду
        setTimeout(() => {
            window.location.reload();
        }, 1000);
        
    } catch (error) {
        console.error('Ошибка синхронизации:', error);
        showNotification('error', 'Ошибка при синхронизации заказов');
        
        // Восстанавливаем кнопку
        button.disabled = false;
        button.innerHTML = originalHTML;
    }
}

/**
 * Фильтрует заказы по статусу
 * @param {string} status - статус для фильтрации ('all' для показа всех)
 */
function filterOrders(status) {
    // Сохраняем текущий статус фильтра
    window.currentStatusFilter = status;
    
    // Сохраняем в localStorage
    localStorage.setItem('orderStatusFilter', status);
    
    // Применяем оба фильтра
    applyFilters();
    
    // Обновляем активную кнопку статуса
    const statusButtons = document.querySelectorAll('.btn-group .btn-outline-primary, .btn-group .btn-outline-info, .btn-group .btn-outline-warning, .btn-group .btn-outline-success, .btn-group .btn-outline-danger');
    statusButtons.forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

/**
 * Фильтрует заказы по статусу получения на складе
 * @param {string} warehouseStatus - 'all', 'received', 'not-received'
 */
function filterWarehouse(warehouseStatus) {
    // Сохраняем текущий статус фильтра склада
    window.currentWarehouseFilter = warehouseStatus;
    
    // Сохраняем в localStorage
    localStorage.setItem('warehouseStatusFilter', warehouseStatus);
    
    // Применяем оба фильтра
    applyFilters();
    
    // Обновляем активную кнопку склада
    const warehouseButtons = document.querySelectorAll('.btn-group .btn-outline-secondary, .btn-group .btn-outline-success, .btn-group .btn-outline-danger');
    warehouseButtons.forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

/**
 * Применяет оба фильтра (статус заказа и склад) одновременно
 */
function applyFilters() {
    const table = document.getElementById('ordersTable');
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    const statusFilter = window.currentStatusFilter || 'all';
    const warehouseFilter = window.currentWarehouseFilter || 'all';
    
    rows.forEach(row => {
        const rowStatus = row.getAttribute('data-status');
        const rowWarehouse = row.getAttribute('data-warehouse');
        
        // Проверяем оба фильтра
        const statusMatch = statusFilter === 'all' || rowStatus === statusFilter;
        const warehouseMatch = warehouseFilter === 'all' || rowWarehouse === warehouseFilter;
        
        if (statusMatch && warehouseMatch) {
            row.classList.remove('hidden');
        } else {
            row.classList.add('hidden');
        }
    });
}

// Инициализируем фильтры при загрузке страницы
window.currentStatusFilter = 'all';
window.currentWarehouseFilter = 'all';

/**
 * Восстанавливает фильтры из localStorage при загрузке страницы
 */
function restoreFilters() {
    // Проверяем, находимся ли мы на странице архива
    const isArchivePage = document.body.getAttribute('data-is-archive') === 'true';
    
    // Восстанавливаем фильтр статуса заказа
    const savedStatusFilter = localStorage.getItem('orderStatusFilter');
    const statusButtons = document.querySelectorAll('.btn-group .btn[onclick*="filterOrders"]');
    
    // На странице архива всегда показываем все статусы
    if (isArchivePage) {
        window.currentStatusFilter = 'all';
    } else if (savedStatusFilter) {
        window.currentStatusFilter = savedStatusFilter;
        
        // Находим и активируем только сохраненную кнопку
        statusButtons.forEach(btn => {
            if (btn.getAttribute('onclick')?.includes(`filterOrders('${savedStatusFilter}')`)) {
                btn.classList.add('active');
            }
        });
    } else {
        // Если фильтр не сохранен - активируем "Все" по умолчанию
        statusButtons.forEach(btn => {
            if (btn.getAttribute('onclick')?.includes(`filterOrders('all')`)) {
                btn.classList.add('active');
            }
        });
    }
    
    // Восстанавливаем фильтр склада
    const savedWarehouseFilter = localStorage.getItem('warehouseStatusFilter');
    const warehouseButtons = document.querySelectorAll('.btn-group .btn[onclick*="filterWarehouse"]');
    
    if (savedWarehouseFilter) {
        window.currentWarehouseFilter = savedWarehouseFilter;
        
        // Находим и активируем только сохраненную кнопку
        warehouseButtons.forEach(btn => {
            if (btn.getAttribute('onclick')?.includes(`filterWarehouse('${savedWarehouseFilter}')`)) {
                btn.classList.add('active');
            }
        });
    } else {
        // Если фильтр не сохранен - активируем "Все" по умолчанию
        warehouseButtons.forEach(btn => {
            if (btn.getAttribute('onclick')?.includes(`filterWarehouse('all')`)) {
                btn.classList.add('active');
            }
        });
    }
    
    // Применяем восстановленные фильтры
    applyFilters();
}

// Вызываем восстановление фильтров при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    restoreFilters();
});

/**
 * Показывает уведомление
 * @param {string} type - тип уведомления ('success', 'error', 'info')
 * @param {string} message - текст сообщения
 */
function showNotification(type, message) {
    // Создаем контейнер для уведомлений, если его нет
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    // Создаем уведомление
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Показываем уведомление
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Удаляем после скрытия
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

/**
 * Форматирует дату для отображения
 * @param {string} dateString - строка с датой
 * @returns {string} отформатированная дата
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    const options = { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return date.toLocaleString('ru-RU', options);
}

/**
 * Копирует трек-номер в буфер обмена
 */
function copyTrackingNumber(trackingNumber) {
    navigator.clipboard.writeText(trackingNumber).then(() => {
        showNotification('success', 'Трек-номер скопирован в буфер обмена');
    }).catch(err => {
        console.error('Ошибка копирования:', err);
    });
}

// Добавляем обработчик клика на трек-номера
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('code').forEach(element => {
        element.style.cursor = 'pointer';
        element.title = 'Нажмите, чтобы скопировать';
        element.addEventListener('click', function() {
            copyTrackingNumber(this.textContent);
        });
    });
});

/**
 * Архивирует заказ
 * @param {string} orderId - ID заказа
 */
async function archiveOrder(orderId) {
    console.log('🗂️ Архивирование заказа:', orderId);
    
    if (!confirm('Переместить этот заказ в архив?')) {
        console.log('❌ Архивирование отменено пользователем');
        return;
    }
    
    try {
        console.log('📤 Отправка запроса на архивирование...');
        const response = await fetch(`/api/orders/${orderId}/archive`, {
            method: 'POST'
        });
        const data = await response.json();
        
        console.log('📥 Ответ сервера:', data);
        
        if (data.status === 'success') {
            showNotification('success', data.message);
            // Перезагружаем страницу через 500мс
            setTimeout(() => {
                window.location.reload();
            }, 500);
        } else {
            showNotification('error', 'Ошибка архивирования заказа');
        }
    } catch (error) {
        console.error('❌ Ошибка:', error);
        showNotification('error', 'Ошибка при архивировании заказа');
    }
}

/**
 * Восстанавливает заказ из архива
 * @param {string} orderId - ID заказа
 */
async function unarchiveOrder(orderId) {
    if (!confirm('Восстановить этот заказ из архива?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/orders/${orderId}/unarchive`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('success', data.message);
            // Перезагружаем страницу через 500мс
            setTimeout(() => {
                window.location.reload();
            }, 500);
        } else {
            showNotification('error', 'Ошибка восстановления заказа');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('error', 'Ошибка при восстановлении заказа');
    }
}

/**
 * Переключает статус "Получен на складе"
 * @param {string} orderId - ID заказа
 * @param {HTMLElement} checkbox - элемент чекбокса
 */
async function toggleWarehouseStatus(orderId, checkbox) {
    try {
        const response = await fetch(`/api/orders/${orderId}/warehouse/toggle`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('success', data.message);
            
            // Обновляем состояние чекбокса согласно ответу сервера
            checkbox.checked = data.received_at_warehouse;
            
            // Обновляем атрибут и класс строки таблицы
            const row = checkbox.closest('tr');
            if (row) {
                const warehouseStatus = data.received_at_warehouse ? 'received' : 'not-received';
                row.setAttribute('data-warehouse', warehouseStatus);
                
                if (data.received_at_warehouse) {
                    row.classList.add('warehouse-received');
                } else {
                    row.classList.remove('warehouse-received');
                }
                
                // Применяем фильтры заново, чтобы строка могла скрыться/показаться
                applyFilters();
            }
        } else {
            showNotification('error', 'Ошибка изменения статуса');
            // Откатываем чекбокс обратно
            checkbox.checked = !checkbox.checked;
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('error', 'Ошибка при изменении статуса');
        // Откатываем чекбокс обратно
        checkbox.checked = !checkbox.checked;
    }
}

/**
 * Переключает выбор всех чекбоксов
 */
function toggleSelectAll(checkbox) {
    const checkboxes = document.querySelectorAll('.order-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = checkbox.checked;
    });
    updateBulkActions();
}

/**
 * Обновляет панель массовых действий
 */
function updateBulkActions() {
    const checkboxes = document.querySelectorAll('.order-checkbox:checked');
    const count = checkboxes.length;
    const bulkActions = document.getElementById('bulkActions');
    const selectedCount = document.getElementById('selectedCount');
    
    if (count > 0) {
        bulkActions.style.display = 'block';
        selectedCount.textContent = `${count} выбрано`;
    } else {
        bulkActions.style.display = 'none';
    }
}

/**
 * Массовое архивирование выбранных заказов
 */
async function archiveSelected() {
    const checkboxes = document.querySelectorAll('.order-checkbox:checked');
    const orderIds = Array.from(checkboxes).map(cb => cb.value);
    
    if (orderIds.length === 0) {
        showNotification('error', 'Не выбраны заказы для архивирования');
        return;
    }
    
    if (!confirm(`Переместить ${orderIds.length} заказов в архив?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/orders/batch/archive', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ order_ids: orderIds })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('success', data.message);
            setTimeout(() => {
                window.location.reload();
            }, 500);
        } else {
            showNotification('error', 'Ошибка архивирования заказов');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('error', 'Ошибка при архивировании заказов');
    }
}

/**
 * Массовое восстановление выбранных заказов
 */
async function unarchiveSelected() {
    const checkboxes = document.querySelectorAll('.order-checkbox:checked');
    const orderIds = Array.from(checkboxes).map(cb => cb.value);
    
    if (orderIds.length === 0) {
        showNotification('error', 'Не выбраны заказы для восстановления');
        return;
    }
    
    if (!confirm(`Восстановить ${orderIds.length} заказов из архива?`)) {
        return;
    }
    
    try {
        // Восстанавливаем через batch unarchive
        const response = await fetch('/api/orders/batch/unarchive', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ order_ids: orderIds })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('success', data.message);
            setTimeout(() => {
                window.location.reload();
            }, 500);
        } else {
            showNotification('error', 'Ошибка восстановления заказов');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('error', 'Ошибка при восстановлении заказов');
    }
}

// Добавляем обработчики для чекбоксов
document.addEventListener('DOMContentLoaded', function() {
    // Обработчик для всех чекбоксов заказов
    const checkboxes = document.querySelectorAll('.order-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateBulkActions);
    });
});

/**
 * Сохраняет заказ, добавленный вручную
 */
async function saveManualOrder() {
    const form = document.getElementById('addOrderForm');
    const button = event.target;
    const originalHTML = button.innerHTML;
    
    // Собираем данные из формы
    const orderData = {
        tracking_number: document.getElementById('trackingNumberInput').value || null,
        supplier_name: document.getElementById('supplierNameInput').value || null,
        description: document.getElementById('descriptionInput').value || null,
        total_price: parseFloat(document.getElementById('priceInput').value) || null,
        currency: document.getElementById('currencyInput').value || 'CNY',
        order_date: document.getElementById('orderDateInput').value || null
    };
    
    // Показываем индикатор загрузки
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Сохранение...';
    
    try {
        const response = await fetch('/api/orders/manual', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Показываем уведомление об успехе
            showNotification('success', 'Заказ успешно добавлен!');
            
            // Закрываем модальное окно
            const modal = bootstrap.Modal.getInstance(document.getElementById('addOrderModal'));
            modal.hide();
            
            // Очищаем форму
            form.reset();
            
            // Перезагружаем страницу через 1 секунду
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification('error', data.detail || 'Ошибка при добавлении заказа');
            button.disabled = false;
            button.innerHTML = originalHTML;
        }
        
    } catch (error) {
        console.error('Ошибка при добавлении заказа:', error);
        showNotification('error', 'Ошибка при добавлении заказа');
        button.disabled = false;
        button.innerHTML = originalHTML;
    }
}

/**
 * Удаляет заказ из базы данных
 */
async function deleteOrder(orderId) {
    // Генерируем простой математический пример
    const num1 = Math.floor(Math.random() * 10) + 1; // 1-10
    const num2 = Math.floor(Math.random() * 10) + 1; // 1-10
    const operations = ['+', '-'];
    const operation = operations[Math.floor(Math.random() * operations.length)];
    
    let correctAnswer;
    if (operation === '+') {
        correctAnswer = num1 + num2;
    } else {
        correctAnswer = num1 - num2;
    }
    
    // Запрашиваем решение примера
    const userAnswer = prompt(`⚠️ ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ\n\nЧтобы удалить заказ, решите пример:\n\n${num1} ${operation} ${num2} = ?`);
    
    // Проверяем ответ
    if (userAnswer === null) {
        // Пользователь отменил
        return;
    }
    
    if (parseInt(userAnswer) !== correctAnswer) {
        showNotification('error', '❌ Неверный ответ. Удаление отменено.');
        return;
    }
    
    try {
        const response = await fetch(`/api/orders/${orderId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('success', 'Заказ успешно удалён');
            
            // Удаляем строку из таблицы с анимацией
            const row = document.querySelector(`tr[data-order-id="${orderId}"]`);
            if (row) {
                row.style.transition = 'opacity 0.3s';
                row.style.opacity = '0';
                setTimeout(() => {
                    row.remove();
                    // Обновляем статистику
                    loadStats();
                }, 300);
            }
        } else {
            showNotification('error', data.detail || 'Ошибка при удалении заказа');
        }
        
    } catch (error) {
        console.error('Ошибка при удалении заказа:', error);
        showNotification('error', 'Ошибка при удалении заказа');
    }
}

/**
 * Открывает модальное окно редактирования заказа
 */
async function openEditModal(orderId) {
    try {
        // Загружаем данные заказа
        const response = await fetch(`/api/orders/${orderId}`);
        const order = await response.json();
        
        if (!response.ok) {
            showNotification('error', 'Ошибка загрузки данных заказа');
            return;
        }
        
        // Заполняем форму
        document.getElementById('editOrderId').value = order.order_id;
        document.getElementById('editTrackingNumberInput').value = order.tracking_number || '';
        document.getElementById('editSupplierNameInput').value = order.translated_description || '';
        document.getElementById('editDescriptionInput').value = order.description || '';
        document.getElementById('editPriceInput').value = order.total_price || '';
        document.getElementById('editCurrencyInput').value = order.currency || 'CNY';
        
        // Форматируем дату для input type="date"
        if (order.order_date) {
            const date = new Date(order.order_date);
            const formattedDate = date.toISOString().split('T')[0];
            document.getElementById('editOrderDateInput').value = formattedDate;
        } else {
            document.getElementById('editOrderDateInput').value = '';
        }
        
        // Открываем модальное окно
        const modal = new bootstrap.Modal(document.getElementById('editOrderModal'));
        modal.show();
        
    } catch (error) {
        console.error('Ошибка при загрузке заказа:', error);
        showNotification('error', 'Ошибка при загрузке заказа');
    }
}

/**
 * Сохраняет изменения заказа
 */
async function saveEditedOrder() {
    const button = event.target;
    const originalHTML = button.innerHTML;
    
    const orderId = document.getElementById('editOrderId').value;
    
    // Собираем данные из формы
    const orderData = {
        tracking_number: document.getElementById('editTrackingNumberInput').value || null,
        supplier_name: document.getElementById('editSupplierNameInput').value || null,
        description: document.getElementById('editDescriptionInput').value || null,
        total_price: parseFloat(document.getElementById('editPriceInput').value) || null,
        currency: document.getElementById('editCurrencyInput').value || 'CNY',
        order_date: document.getElementById('editOrderDateInput').value || null
    };
    
    // Показываем индикатор загрузки
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Сохранение...';
    
    try {
        const response = await fetch(`/api/orders/${orderId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('success', 'Изменения сохранены!');
            
            // Закрываем модальное окно
            const modal = bootstrap.Modal.getInstance(document.getElementById('editOrderModal'));
            modal.hide();
            
            // Перезагружаем страницу через 1 секунду
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification('error', data.detail || 'Ошибка при сохранении изменений');
            button.disabled = false;
            button.innerHTML = originalHTML;
        }
        
    } catch (error) {
        console.error('Ошибка при сохранении изменений:', error);
        showNotification('error', 'Ошибка при сохранении изменений');
        button.disabled = false;
        button.innerHTML = originalHTML;
    }
}
