// Sistema de Inventario - JavaScript
document.addEventListener('DOMContentLoaded', function() {
    
    // Inicializar componentes
    initFlashMessages();
    initTooltips();
    initFormValidation();
    initSearchFunctionality();
    initTableSorting();
    
    // Auto-cerrar mensajes flash después de 5 segundos
    function initFlashMessages() {
        const flashMessages = document.querySelectorAll('.flash');
        flashMessages.forEach(message => {
            setTimeout(() => {
                if (message.parentNode) {
                    message.style.opacity = '0';
                    message.style.transform = 'translateY(-20px)';
                    setTimeout(() => {
                        message.remove();
                    }, 300);
                }
            }, 5000);
        });
    }
    
    // Tooltips para botones
    function initTooltips() {
        const tooltips = document.querySelectorAll('[title]');
        tooltips.forEach(element => {
            element.addEventListener('mouseenter', showTooltip);
            element.addEventListener('mouseleave', hideTooltip);
        });
    }
    
    function showTooltip(event) {
        const element = event.target;
        const title = element.getAttribute('title');
        
        if (!title) return;
        
        // Crear tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = title;
        tooltip.style.cssText = `
            position: absolute;
            background: #333;
            color: white;
            padding: 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            z-index: 1000;
            pointer-events: none;
            white-space: nowrap;
            opacity: 0;
            transition: opacity 0.3s;
        `;
        
        document.body.appendChild(tooltip);
        
        // Posicionar tooltip
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
        
        // Mostrar tooltip
        setTimeout(() => {
            tooltip.style.opacity = '1';
        }, 100);
        
        // Guardar referencia para poder eliminarlo
        element._tooltip = tooltip;
        
        // Remover title para evitar tooltip nativo
        element.setAttribute('data-original-title', title);
        element.removeAttribute('title');
    }
    
    function hideTooltip(event) {
        const element = event.target;
        if (element._tooltip) {
            element._tooltip.remove();
            element._tooltip = null;
        }
        
        // Restaurar title
        const originalTitle = element.getAttribute('data-original-title');
        if (originalTitle) {
            element.setAttribute('title', originalTitle);
            element.removeAttribute('data-original-title');
        }
    }
    
    // Validación de formularios
    function initFormValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', validateForm);
            
            // Validación en tiempo real
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('blur', validateField);
                input.addEventListener('input', clearFieldError);
            });
        });
    }
    
    function validateForm(event) {
        const form = event.target;
        let isValid = true;
        
        // Validar campos requeridos
        const requiredFields = form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (!validateField({ target: field })) {
                isValid = false;
            }
        });
        
        // Validaciones específicas
        const nombreField = form.querySelector('[name="nombre"]');
        if (nombreField && nombreField.value.trim().length < 2) {
            showFieldError(nombreField, 'El nombre debe tener al menos 2 caracteres');
            isValid = false;
        }
        
        const cantidadField = form.querySelector('[name="cantidad"]');
        if (cantidadField && parseInt(cantidadField.value) < 0) {
            showFieldError(cantidadField, 'La cantidad no puede ser negativa');
            isValid = false;
        }
        
        const precioField = form.querySelector('[name="precio"]');
        if (precioField && parseFloat(precioField.value) < 0) {
            showFieldError(precioField, 'El precio no puede ser negativo');
            isValid = false;
        }
        
        if (!isValid) {
            event.preventDefault();
            showNotification('Por favor, corrija los errores en el formulario', 'error');
        }
    }
    
    function validateField(event) {
        const field = event.target;
        clearFieldError(event);
        
        if (field.hasAttribute('required') && !field.value.trim()) {
            showFieldError(field, 'Este campo es obligatorio');
            return false;
        }
        
        if (field.type === 'email' && field.value && !isValidEmail(field.value)) {
            showFieldError(field, 'Ingrese un email válido');
            return false;
        }
        
        if (field.type === 'number' && field.value && isNaN(field.value)) {
            showFieldError(field, 'Ingrese un número válido');
            return false;
        }
        
        return true;
    }
    
    function clearFieldError(event) {
        const field = event.target;
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
        field.classList.remove('error');
    }
    
    function showFieldError(field, message) {
        clearFieldError({ target: field });
        
        field.classList.add('error');
        
        const errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        errorElement.textContent = message;
        errorElement.style.cssText = `
            color: var(--danger-color);
            font-size: 0.8rem;
            margin-top: 0.25rem;
            display: block;
        `;
        
        field.parentNode.appendChild(errorElement);
    }
    
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    // Funcionalidad de búsqueda
    function initSearchFunctionality() {
        const searchInput = document.querySelector('#q');
        const searchForm = document.querySelector('.search-form-advanced');
        
        if (searchInput) {
            // Auto-focus en campos de búsqueda
            searchInput.focus();
            
            // Búsqueda con Enter
            searchInput.addEventListener('keypress', function(event) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    if (searchForm) {
                        searchForm.submit();
                    }
                }
            });
            
            // Limpiar búsqueda
            const clearButton = document.createElement('button');
            clearButton.type = 'button';
            clearButton.className = 'btn btn-secondary btn-sm';
            clearButton.innerHTML = '<i class="fas fa-times"></i> Limpiar';
            clearButton.addEventListener('click', function() {
                searchInput.value = '';
                searchInput.focus();
            });
            
            if (searchInput.value) {
                searchInput.parentNode.appendChild(clearButton);
            }
        }
    }
    
    // Ordenamiento de tablas
    function initTableSorting() {
        const tables = document.querySelectorAll('.products-table');
        tables.forEach(table => {
            const headers = table.querySelectorAll('th');
            headers.forEach((header, index) => {
                if (header.textContent.trim() && index < headers.length - 1) { // No ordenar la columna de acciones
                    header.style.cursor = 'pointer';
                    header.addEventListener('click', () => sortTable(table, index));
                    
                    // Añadir icono de ordenamiento
                    const sortIcon = document.createElement('i');
                    sortIcon.className = 'fas fa-sort sort-icon';
                    sortIcon.style.marginLeft = '0.5rem';
                    header.appendChild(sortIcon);
                }
            });
        });
    }
    
    function sortTable(table, columnIndex) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const header = table.querySelectorAll('th')[columnIndex];
        const sortIcon = header.querySelector('.sort-icon');
        
        // Determinar dirección de ordenamiento
        const isAscending = !header.classList.contains('sorted-asc');
        
        // Limpiar iconos de ordenamiento previos
        table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sorted-asc', 'sorted-desc');
            const icon = th.querySelector('.sort-icon');
            if (icon) {
                icon.className = 'fas fa-sort sort-icon';
            }
        });
        
        // Ordenar filas
        rows.sort((a, b) => {
            const aValue = getCellValue(a, columnIndex);
            const bValue = getCellValue(b, columnIndex);
            
            // Ordenamiento numérico para precios y cantidades
            if (!isNaN(aValue) && !isNaN(bValue)) {
                return isAscending ? aValue - bValue : bValue - aValue;
            }
            
            // Ordenamiento alfabético
            return isAscending 
                ? aValue.localeCompare(bValue)
                : bValue.localeCompare(aValue);
        });
        
        // Aplicar ordenamiento
        rows.forEach(row => tbody.appendChild(row));
        
        // Actualizar icono
        header.classList.add(isAscending ? 'sorted-asc' : 'sorted-desc');
        sortIcon.className = `fas fa-sort-${isAscending ? 'up' : 'down'} sort-icon`;
    }
    
    function getCellValue(row, columnIndex) {
        const cell = row.cells[columnIndex];
        const text = cell.textContent.trim();
        
        // Extraer números de texto (para precios con $)
        const numberMatch = text.match(/[\d,]+\.?\d*/);
        if (numberMatch) {
            return parseFloat(numberMatch[0].replace(/,/g, ''));
        }
        
        return text.toLowerCase();
    }
});

// Funciones globales para modales y confirmaciones
function deleteProduct(productId, productName) {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        const productNameElement = document.getElementById('productName');
        const deleteForm = document.getElementById('deleteForm');
        
        if (productNameElement) {
            productNameElement.textContent = productName;
        }
        
        if (deleteForm) {
            deleteForm.action = `/producto/${productId}/eliminar`;
        }
        
        modal.style.display = 'block';
        
        // Enfocar el botón de cancelar para mejor UX
        const cancelButton = modal.querySelector('.btn-secondary');
        if (cancelButton) {
            cancelButton.focus();
        }
    }
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Cerrar modales con Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (modal.style.display === 'block') {
                modal.style.display = 'none';
            }
        });
    }
});

// Cerrar modales al hacer clic fuera
window.addEventListener('click', function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});

// Sistema de notificaciones
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // Estilos para la notificación
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        z-index: 1001;
        min-width: 300px;
        animation: slideInRight 0.3s ease-out;
        border-left: 4px solid var(--${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'}-color);
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remover después del tiempo especificado
    if (duration > 0) {
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, duration);
    }
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Funciones utilitarias
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Funciones para el formulario de productos
function updateTotalValue() {
    const cantidadInput = document.getElementById('cantidad');
    const precioInput = document.getElementById('precio');
    const totalElement = document.getElementById('totalValue');
    
    if (cantidadInput && precioInput && totalElement) {
        const cantidad = parseFloat(cantidadInput.value) || 0;
        const precio = parseFloat(precioInput.value) || 0;
        const total = cantidad * precio;
        
        totalElement.textContent = formatCurrency(total);
        
        // Actualizar color basado en el valor
        if (total > 1000) {
            totalElement.style.color = 'var(--success-color)';
        } else if (total > 500) {
            totalElement.style.color = 'var(--warning-color)';
        } else {
            totalElement.style.color = 'var(--text-color)';
        }
    }
}

// Auto-completado para categorías
function initCategoryAutocomplete() {
    const categoryInput = document.getElementById('categoria');
    if (categoryInput) {
        const datalist = document.getElementById('categorias');
        const options = Array.from(datalist.querySelectorAll('option')).map(option => option.value);
        
        categoryInput.addEventListener('input', function() {
            const value = this.value.toLowerCase();
            const matches = options.filter(option => 
                option.toLowerCase().includes(value)
            );
            
            // Actualizar datalist
            datalist.innerHTML = '';
            matches.forEach(match => {
                const option = document.createElement('option');
                option.value = match;
                datalist.appendChild(option);
            });
        });
    }
}

// Inicializar auto-completado cuando se carga la página
document.addEventListener('DOMContentLoaded', initCategoryAutocomplete);

// Función para exportar datos (funcionalidad adicional)
function exportToCSV(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = Array.from(table.querySelectorAll('tr'));
    const csv = rows.map(row => {
        const cells = Array.from(row.querySelectorAll('th, td'));
        return cells.map(cell => {
            // Limpiar texto de la celda
            const text = cell.textContent.trim().replace(/"/g, '""');
            return `"${text}"`;
        }).join(',');
    }).join('\n');
    
    // Crear y descargar archivo
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'inventario.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Función para imprimir tabla
function printTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write('<html><head><title>Inventario</title>');
    printWindow.document.write('<style>');
    printWindow.document.write('table { border-collapse: collapse; width: 100%; }');
    printWindow.document.write('th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }');
    printWindow.document.write('th { background-color: #f2f2f2; }');
    printWindow.document.write('</style></head><body>');
    printWindow.document.write('<h1>Sistema de Inventario</h1>');
    printWindow.document.write(table.outerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

// Añadir estilos CSS para las animaciones y notificaciones
const additionalCSS = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .notification-content {
        padding: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .notification-close {
        background: none;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
        color: #666;
        margin-left: auto;
    }
    
    .notification-close:hover {
        color: #333;
    }
    
    .form-input.error,
    .form-textarea.error,
    .form-select.error {
        border-color: var(--danger-color);
        box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.1);
    }
    
    .sort-icon {
        opacity: 0.5;
        transition: opacity 0.3s;
    }
    
    th:hover .sort-icon {
        opacity: 1;
    }
    
    th.sorted-asc .sort-icon,
    th.sorted-desc .sort-icon {
        opacity: 1;
        color: var(--primary-color);
    }
`;

// Inyectar CSS adicional
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalCSS;
document.head.appendChild(styleSheet);