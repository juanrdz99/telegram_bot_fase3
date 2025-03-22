/**
 * Liga MX Bot - JavaScript principal
 * 
 * Este archivo contiene funciones compartidas entre todas las páginas
 * de la aplicación web de Liga MX Bot, incluyendo utilidades para
 * formateo de fechas y horas, gestión de peticiones API y más.
 */

// Configuración global
const CONFIG = {
    TIMEZONE: 'America/Mexico_City', // UTC-6
    LOCALE: 'es-MX',
    REFRESH_INTERVAL: 60000 // 1 minuto
};

// Elementos DOM comunes
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips si existen
    initTooltips();
    
    // Actualizar fecha y hora actual en la barra de estado si existe
    updateCurrentDateTime();
    
    // Configurar peticiones AJAX globales
    setupAjaxHandlers();
});

/**
 * Inicializa tooltips en elementos con atributo data-tooltip
 */
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    if (tooltips.length > 0) {
        tooltips.forEach(el => {
            el.addEventListener('mouseenter', showTooltip);
            el.addEventListener('mouseleave', hideTooltip);
        });
    }
}

/**
 * Muestra un tooltip
 */
function showTooltip(e) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = this.getAttribute('data-tooltip');
    document.body.appendChild(tooltip);
    
    const rect = this.getBoundingClientRect();
    tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
    
    setTimeout(() => tooltip.classList.add('visible'), 10);
}

/**
 * Oculta un tooltip
 */
function hideTooltip(e) {
    const tooltips = document.querySelectorAll('.tooltip.visible');
    tooltips.forEach(t => {
        t.classList.remove('visible');
        setTimeout(() => t.remove(), 200);
    });
}

/**
 * Actualiza la fecha y hora actuales en un elemento con ID 'current-time'
 */
function updateCurrentDateTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const updateTime = () => {
            const now = new Date();
            const options = { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                timeZone: CONFIG.TIMEZONE
            };
            timeElement.textContent = now.toLocaleDateString(CONFIG.LOCALE, options);
        };
        
        updateTime();
        setInterval(updateTime, 1000);
    }
}

/**
 * Configura manejadores globales para peticiones AJAX
 */
function setupAjaxHandlers() {
    // Interceptar errores globales de fetch
    window.addEventListener('unhandledrejection', function(event) {
        if (event.reason && typeof event.reason.message === 'string') {
            console.error('Error no manejado en promesa:', event.reason.message);
            showNotification('Error de conexión. Por favor intente nuevamente.', 'error');
        }
    });
}

/**
 * Muestra una notificación en la parte superior de la página
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo de notificación ('success', 'error', 'warning', 'info')
 * @param {number} duration - Duración en milisegundos
 */
function showNotification(message, type = 'info', duration = 5000) {
    // Comprobar si ya existe un contenedor de notificaciones
    let container = document.querySelector('.notification-container');
    
    if (!container) {
        container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    
    // Crear notificación
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Icono según tipo
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas fa-${icon}"></i>
        </div>
        <div class="notification-content">${message}</div>
        <button class="notification-close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Agregar al contenedor
    container.appendChild(notification);
    
    // Hacer visible
    setTimeout(() => notification.classList.add('visible'), 10);
    
    // Configurar botón de cierre
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        hideNotification(notification);
    });
    
    // Ocultar automáticamente después de la duración
    if (duration > 0) {
        setTimeout(() => {
            hideNotification(notification);
        }, duration);
    }
    
    return notification;
}

/**
 * Oculta una notificación
 * @param {HTMLElement} notification - Elemento de notificación a ocultar
 */
function hideNotification(notification) {
    notification.classList.remove('visible');
    setTimeout(() => {
        notification.remove();
        
        // Eliminar contenedor si no hay más notificaciones
        const container = document.querySelector('.notification-container');
        if (container && container.children.length === 0) {
            container.remove();
        }
    }, 300);
}

/**
 * Formatea una fecha
 * @param {string} dateString - Fecha en formato ISO (YYYY-MM-DD)
 * @param {object} options - Opciones de formato
 * @returns {string} Fecha formateada
 */
function formatDate(dateString, options = {}) {
    if (!dateString) return 'Fecha no disponible';
    
    const defaultOptions = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    
    const formatOptions = { ...defaultOptions, ...options };
    const date = new Date(dateString);
    
    return date.toLocaleDateString(CONFIG.LOCALE, formatOptions);
}

/**
 * Formatea una hora
 * @param {string} timeString - Hora en formato HH:MM
 * @returns {string} Hora formateada
 */
function formatTime(timeString) {
    if (!timeString) return 'Hora no disponible';
    
    // Parsear la hora
    const [hours, minutes] = timeString.split(':').map(Number);
    
    // Determinar AM/PM
    const period = hours >= 12 ? 'p.m.' : 'a.m.';
    
    // Convertir a formato de 12 horas
    const hours12 = hours % 12 || 12;
    
    // Formatear hora
    return `${hours12}:${minutes.toString().padStart(2, '0')} ${period}`;
}

/**
 * Formatea un día de la semana
 * @param {Date} date - Objeto Date
 * @param {boolean} abbreviated - Si es true, devuelve el formato abreviado
 * @returns {string} Día de la semana
 */
function formatWeekday(date, abbreviated = false) {
    if (!date) return '';
    
    const options = { 
        weekday: abbreviated ? 'short' : 'long'
    };
    
    return date.toLocaleDateString(CONFIG.LOCALE, options);
}

/**
 * Realiza una solicitud fetch con manejo de errores
 * @param {string} url - URL a la que hacer la petición
 * @param {object} options - Opciones de fetch
 * @returns {Promise} Promesa con los datos de respuesta
 */
function fetchWithErrorHandling(url, options = {}) {
    return fetch(url, options)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Error en fetch:', error);
            showNotification(`Error: ${error.message}`, 'error');
            throw error;
        });
}

/**
 * Crea un elemento DOM con clases y atributos
 * @param {string} tag - Etiqueta HTML
 * @param {object} options - Opciones como classes, attrs, text, html
 * @returns {HTMLElement} Elemento creado
 */
function createElement(tag, options = {}) {
    const element = document.createElement(tag);
    
    if (options.classes) {
        if (Array.isArray(options.classes)) {
            element.classList.add(...options.classes);
        } else {
            element.className = options.classes;
        }
    }
    
    if (options.attrs) {
        for (const [key, value] of Object.entries(options.attrs)) {
            element.setAttribute(key, value);
        }
    }
    
    if (options.text) {
        element.textContent = options.text;
    }
    
    if (options.html) {
        element.innerHTML = options.html;
    }
    
    return element;
}

/**
 * Genera una URL segura para obtener un logo de equipo
 * @param {string} teamName - Nombre del equipo
 * @returns {string} URL del logo
 */
function getTeamLogoUrl(teamName) {
    const defaultLogo = '/static/img/ligamx/default.png';
    
    if (!teamName) return defaultLogo;
    
    // Normalizar el nombre del equipo
    const normalizedName = teamName.toLowerCase().trim()
        .normalize("NFD").replace(/[\u0300-\u036f]/g, "") // Eliminar acentos
        .replace(/[^a-z0-9]/g, ""); // Eliminar caracteres especiales
    
    // Mapeo de nombres de equipos a archivos de imagen
    const teamMap = {
        'america': 'america',
        'atlas': 'atlas',
        'atleticosanluis': 'sanluis',
        'cruzazul': 'cruzazul',
        'guadalajara': 'guadalajara',
        'chivas': 'guadalajara',
        'juarez': 'juarez',
        'leon': 'leon',
        'mazatlan': 'mazatlan',
        'monterrey': 'monterrey',
        'necaxa': 'necaxa',
        'pachuca': 'pachuca',
        'puebla': 'puebla',
        'pumas': 'pumas',
        'pumasunam': 'pumas',
        'queretaro': 'queretaro',
        'santoslaguna': 'santos',
        'santos': 'santos',
        'tigres': 'tigres',
        'tigresuanl': 'tigres',
        'tijuana': 'tijuana',
        'xolos': 'tijuana',
        'toluca': 'toluca'
    };
    
    // Buscar coincidencia
    let logoName = null;
    for (const [key, value] of Object.entries(teamMap)) {
        if (normalizedName.includes(key)) {
            logoName = value;
            break;
        }
    }
    
    return logoName ? `/static/img/ligamx/${logoName}.png` : defaultLogo;
}
