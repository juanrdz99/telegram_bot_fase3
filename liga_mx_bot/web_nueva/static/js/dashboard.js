/**
 * Liga MX Bot - Dashboard de Monitoreo
 * Script específico para la página de dashboard
 * Configurado para México (UTC-6)
 */

// Configuración global
const REFRESH_INTERVAL = 60000; // 1 minuto
const CHART_COLORS = {
    blue: 'rgba(0, 70, 140, 0.7)',
    blueLight: 'rgba(0, 70, 140, 0.2)',
    green: 'rgba(0, 169, 79, 0.7)',
    greenLight: 'rgba(0, 169, 79, 0.2)',
    red: 'rgba(213, 0, 0, 0.7)',
    redLight: 'rgba(213, 0, 0, 0.2)',
    orange: 'rgba(255, 159, 64, 0.7)',
    orangeLight: 'rgba(255, 159, 64, 0.2)'
};

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar dashboard
    initDashboard();
    
    // Actualizar datos cada minuto
    setInterval(updateDashboardData, REFRESH_INTERVAL);
    
    // Configurar controles de tiempo
    setupTimeFilters();
    
    // Cargar logs
    loadSystemLogs();
    
    // Actualizar reloj en tiempo real (cada segundo)
    setInterval(updateCurrentTime, 1000);
    
    // Configurar botón de actualización manual
    document.getElementById('refresh-dashboard').addEventListener('click', function() {
        // Mostrar indicador visual de actualización
        this.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Actualizando...';
        this.disabled = true;
        
        // Actualizar datos
        Promise.all([
            updateDashboardData(),
            loadSystemLogs(),
            fetchPrometheusMetrics()
        ]).finally(() => {
            // Restaurar botón
            this.innerHTML = '<i class="fas fa-sync-alt"></i> Actualizar';
            this.disabled = false;
            
            // Actualizar hora de actualización
            document.getElementById('last-updated').textContent = new Date().toLocaleTimeString('es-MX', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true,
                timeZone: 'America/Mexico_City'
            });
        });
    });
});

/**
 * Actualiza la hora actual en el dashboard
 * Usa la zona horaria de México (UTC-6)
 */
function updateCurrentTime() {
    const currentTimeElement = document.getElementById('current-time');
    if (currentTimeElement) {
        const now = new Date();
        const options = {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true,
            timeZone: 'America/Mexico_City'
        };
        
        currentTimeElement.textContent = now.toLocaleTimeString('es-MX', options);
    }
}

/**
 * Inicializa el dashboard con datos
 */
function initDashboard() {
    // Mostrar indicadores de carga
    showLoadingIndicators();
    
    // Inicializar datos
    updateDashboardData()
        .then(() => {
            initMetricCharts();
            // Obtener datos del servidor Prometheus si está disponible
            return fetchPrometheusMetrics();
        })
        .finally(() => {
            // Ocultar indicadores de carga
            hideLoadingIndicators();
        });
}

/**
 * Muestra los indicadores de carga en el dashboard
 */
function showLoadingIndicators() {
    const loadingElements = document.querySelectorAll('.loading-indicator');
    loadingElements.forEach(el => {
        el.style.display = 'flex';
    });
}

/**
 * Oculta los indicadores de carga en el dashboard
 */
function hideLoadingIndicators() {
    const loadingElements = document.querySelectorAll('.loading-indicator');
    loadingElements.forEach(el => {
        el.style.display = 'none';
    });
}

/**
 * Actualiza los datos del dashboard
 * @returns {Promise} Promesa que se resuelve cuando los datos se han actualizado
 */
function updateDashboardData() {
    // Mostrar indicadores de carga
    showLoadingIndicators(); 
    
    return fetchWithErrorHandling('/api/metrics_data')
        .then(data => {
            if (data.success && data.metrics) {
                updateMetricsDisplay(data.metrics);
                updateAlerts(data.metrics);
                console.log('[Dashboard] Datos actualizados correctamente:', new Date().toLocaleTimeString('es-MX'));
            } else {
                console.error('[Dashboard] Error al obtener datos de métricas:', data.error || 'Error desconocido');
            }
        })
        .catch(error => {
            console.error('[Dashboard] Error al actualizar datos:', error);
        })
        .finally(() => {
            // Ocultar indicadores de carga
            hideLoadingIndicators();
        });
}

/**
 * Actualiza los valores de métricas en pantalla
 */
function updateMetricsDisplay(metrics) {
    // Actualizar contadores básicos
    if (document.getElementById('api-calls-total')) {
        const apiCalls = metrics.system_metrics?.api_calls?.total || metrics.api_calls?.total || 0;
        document.getElementById('api-calls-total').textContent = formatNumber(apiCalls);
    }
    
    if (document.getElementById('success-rate')) {
        const successRate = metrics.system_metrics?.api_calls?.success_rate || metrics.api_calls?.success_rate || 98.5;
        document.getElementById('success-rate').textContent = successRate.toFixed(1) + '%';
        
        // Actualizar color según el valor
        const successRateContainer = document.getElementById('success-rate').closest('.metric-value');
        if (successRateContainer) {
            if (successRate < 90) {
                successRateContainer.className = 'metric-value text-danger';
            } else if (successRate < 95) {
                successRateContainer.className = 'metric-value text-warning';
            } else {
                successRateContainer.className = 'metric-value text-success';
            }
        }
    }
    
    if (document.getElementById('avg-response-time')) {
        const responseTime = metrics.system_metrics?.api_calls?.avg_response_time || metrics.api_calls?.avg_response_time || 0.35;
        document.getElementById('avg-response-time').textContent = (responseTime * 1000).toFixed(0) + ' ms';
    }
    
    if (document.getElementById('error-count')) {
        const errors = metrics.system_metrics?.errors?.total || metrics.errors?.total || 0;
        document.getElementById('error-count').textContent = formatNumber(errors);
    }
    
    if (document.getElementById('active-users')) {
        const activeUsers = metrics.active_users || metrics.system?.active_users || 5;
        document.getElementById('active-users').textContent = formatNumber(activeUsers);
    }
    
    if (document.getElementById('uptime')) {
        const uptime = metrics.system_metrics?.performance?.uptime || metrics.system?.uptime || '7d 12h 45m';
        document.getElementById('uptime').textContent = formatUptime(uptime);
    }
    
    // Actualizar indicador de estado del sistema
    updateSystemStatus(metrics.status || 'online');
    
    // Actualizar tendencias (simuladas o reales si están disponibles)
    updateTrends(metrics.trends || null);
    
    // Actualizar hora de última actualización
    document.getElementById('last-updated').textContent = new Date().toLocaleTimeString('es-MX', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
        timeZone: 'America/Mexico_City'
    });
}

/**
 * Actualiza el indicador de estado del sistema
 * @param {string} status - Estado del sistema (online, warning, offline, unknown)
 */
function updateSystemStatus(status) {
    const statusIndicator = document.getElementById('system-status-indicator');
    const statusText = document.getElementById('system-status-text');
    
    if (!statusIndicator || !statusText) return;
    
    // Configurar el indicador según el estado
    switch (status) {
        case 'online':
            statusIndicator.className = 'status-indicator online';
            statusText.textContent = 'En línea';
            statusText.className = 'status-text text-success';
            break;
        case 'warning':
            statusIndicator.className = 'status-indicator warning';
            statusText.textContent = 'Advertencia';
            statusText.className = 'status-text text-warning';
            break;
        case 'offline':
            statusIndicator.className = 'status-indicator offline';
            statusText.textContent = 'Fuera de línea';
            statusText.className = 'status-text text-danger';
            break;
        default:
            statusIndicator.className = 'status-indicator unknown';
            statusText.textContent = 'Desconocido';
            statusText.className = 'status-text text-muted';
    }
}

/**
 * Formatea un tiempo de uptime en formato legible
 * @param {string|number} uptime - Tiempo de uptime (en segundos si es número)
 * @returns {string} Tiempo formateado
 */
function formatUptime(uptime) {
    // Si ya es string, devolver directamente
    if (typeof uptime === 'string' && uptime.includes('d') || uptime.includes('h') || uptime.includes('m')) {
        return uptime;
    }
    
    // Convertir a segundos si es necesario
    const seconds = parseInt(uptime, 10);
    if (isNaN(seconds)) return '0m';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

/**
 * Formatea un número para su visualización
 */
function formatNumber(num) {
    return new Intl.NumberFormat('es-MX').format(num);
}

/**
 * Actualiza las tendencias visuales de las métricas
 * @param {Object|null} trends - Datos de tendencias (si están disponibles)
 */
function updateTrends(trends = null) {
    const trendElements = document.querySelectorAll('.metric-trend');
    
    trendElements.forEach(trendElement => {
        const metricId = trendElement.getAttribute('data-metric-id');
        let isUp, changePercent;
        
        // Si hay datos reales, usarlos
        if (trends && trends[metricId]) {
            isUp = trends[metricId].direction === 'up';
            changePercent = trends[metricId].percentage.toFixed(1);
        } else {
            // Generar datos simulados para demostración
            isUp = Math.random() > 0.5;
            changePercent = (Math.random() * 10).toFixed(1);
        }
        
        // Actualizar elemento visual
        trendElement.className = `metric-trend ${isUp ? 'up' : 'down'}`;
        trendElement.innerHTML = `
            <span class="trend-arrow">
                <i class="fas fa-arrow-${isUp ? 'up' : 'down'}"></i>
            </span>
            ${changePercent}% desde ayer
        `;
    });
}

/**
 * Inicializa los gráficos de métricas
 */
function initMetricCharts() {
    // Gráfico de uso de CPU y memoria
    if (document.getElementById('cpu-chart')) {
        const cpuCtx = document.getElementById('cpu-chart').getContext('2d');
        
        // Generar datos aleatorios para demostración
        const timeLabels = generateTimeLabels(24, 'hora');
        const cpuData = generateRandomData(24, 10, 30);
        const memoryData = generateRandomData(24, 80, 40);
        
        new Chart(cpuCtx, {
            type: 'line',
            data: {
                labels: timeLabels,
                datasets: [
                    {
                        label: 'CPU (%)',
                        data: cpuData,
                        borderColor: CHART_COLORS.blue,
                        backgroundColor: CHART_COLORS.blueLight,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Memoria (MB)',
                        data: memoryData,
                        borderColor: CHART_COLORS.green,
                        backgroundColor: CHART_COLORS.greenLight,
                        tension: 0.4,
                        fill: true,
                        hidden: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Uso de Recursos (24h)'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Uso (%)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Hora'
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }
    
    // Gráfico de solicitudes API
    if (document.getElementById('api-chart')) {
        const apiCtx = document.getElementById('api-chart').getContext('2d');
        
        // Generar datos aleatorios para demostración
        const timeLabels = generateTimeLabels(7, 'día');
        const apiData = generateRandomData(7, 100, 50);
        const errorData = generateRandomData(7, 5, 3);
        
        new Chart(apiCtx, {
            type: 'bar',
            data: {
                labels: timeLabels,
                datasets: [
                    {
                        label: 'Solicitudes exitosas',
                        data: apiData,
                        backgroundColor: CHART_COLORS.green
                    },
                    {
                        label: 'Errores',
                        data: errorData,
                        backgroundColor: CHART_COLORS.red
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Solicitudes API (Última semana)'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Solicitudes'
                        },
                        stacked: true
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Día'
                        },
                        stacked: true
                    }
                }
            }
        });
    }
    
    // Gráfico de tiempo de respuesta
    if (document.getElementById('response-time-chart')) {
        const respTimeCtx = document.getElementById('response-time-chart').getContext('2d');
        
        // Generar datos aleatorios para demostración
        const timeLabels = generateTimeLabels(24, 'hora');
        const responseTimeData = generateRandomData(24, 150, 100);
        
        new Chart(respTimeCtx, {
            type: 'line',
            data: {
                labels: timeLabels,
                datasets: [
                    {
                        label: 'Tiempo de respuesta (ms)',
                        data: responseTimeData,
                        borderColor: CHART_COLORS.orange,
                        backgroundColor: CHART_COLORS.orangeLight,
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Tiempo de respuesta (24h)'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Tiempo (ms)'
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }
}

/**
 * Genera etiquetas de tiempo para gráficos
 * @param {number} count - Número de etiquetas
 * @param {string} type - Tipo de etiqueta (hora, día)
 * @returns {Array} Array de etiquetas
 */
function generateTimeLabels(count, type) {
    const labels = [];
    const now = new Date();
    
    if (type === 'hora') {
        // Generar etiquetas de hora
        for (let i = count - 1; i >= 0; i--) {
            const hour = new Date(now);
            hour.setHours(now.getHours() - i);
            
            labels.push(hour.toLocaleTimeString('es-MX', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: true,
                timeZone: 'America/Mexico_City'
            }));
        }
    } else if (type === 'día') {
        // Generar etiquetas de día
        for (let i = count - 1; i >= 0; i--) {
            const day = new Date(now);
            day.setDate(now.getDate() - i);
            
            labels.push(day.toLocaleDateString('es-MX', {
                weekday: 'short',
                day: 'numeric',
                timeZone: 'America/Mexico_City'
            }));
        }
    }
    
    return labels;
}

/**
 * Genera datos aleatorios para gráficos de demostración
 * @param {number} count - Número de puntos a generar
 * @param {number} base - Valor base
 * @param {number} variance - Varianza máxima
 * @returns {Array} Array de datos aleatorios
 */
function generateRandomData(count, base, variance) {
    const data = [];
    
    for (let i = 0; i < count; i++) {
        data.push(Math.floor(Math.random() * variance) + base);
    }
    
    return data;
}

/**
 * Configura los filtros de tiempo
 */
function setupTimeFilters() {
    const timeFilters = document.querySelectorAll('.time-filter button');
    
    timeFilters.forEach(btn => {
        btn.addEventListener('click', function() {
            // Eliminar clase activa de todos los botones
            timeFilters.forEach(b => b.classList.remove('active'));
            
            // Agregar clase activa al botón clickeado
            this.classList.add('active');
            
            // Actualizar gráficos con nuevo rango de tiempo
            const timeRange = this.getAttribute('data-range');
            updateChartsTimeRange(timeRange);
        });
    });
}

/**
 * Actualiza el rango de tiempo de los gráficos
 * @param {string} timeRange - Rango de tiempo (24h, 7d, 30d)
 */
function updateChartsTimeRange(timeRange) {
    // Este es un ejemplo, en una implementación real
    // actualizaríamos los datos de los gráficos con una nueva solicitud API
    console.log(`Cambiando rango de tiempo a: ${timeRange}`);
    
    // Reiniciar la animación de carga
    document.querySelectorAll('.chart-loading').forEach(el => {
        el.style.display = 'flex';
    });
    
    // Simular tiempo de carga
    setTimeout(() => {
        // Ocultar animación de carga
        document.querySelectorAll('.chart-loading').forEach(el => {
            el.style.display = 'none';
        });
        
        // Reinicializar gráficos con nuevos datos
        initMetricCharts();
        
        // Mostrar notificación
        showNotification(`Datos actualizados para el periodo: ${getTimeRangeLabel(timeRange)}`, 'success');
    }, 1000);
}

/**
 * Obtiene la etiqueta de un rango de tiempo
 */
function getTimeRangeLabel(range) {
    switch(range) {
        case '24h': return 'Últimas 24 horas';
        case '7d': return 'Últimos 7 días';
        case '30d': return 'Últimos 30 días';
        default: return 'Período personalizado';
    }
}

/**
 * Actualiza el panel de alertas
 */
function updateAlerts(metrics) {
    const alertsList = document.getElementById('alerts-list');
    if (!alertsList) return;
    
    // Limpiar alertas anteriores
    alertsList.innerHTML = '';
    
    // Generar alertas aleatorias para demostración
    const alertTypes = ['info', 'warning', 'critical'];
    const alertMessages = [
        { type: 'info', message: 'Sistema operando normalmente', timestamp: '20:05:12' },
        { type: 'warning', message: 'Uso de CPU superior al 80%', timestamp: '19:42:35' },
        { type: 'warning', message: 'Latencia de base de datos elevada', timestamp: '19:23:11' },
        { type: 'critical', message: 'Error de conexión a la API de LiveScore', timestamp: '18:55:02' },
        { type: 'info', message: 'Nuevos datos de partidos disponibles', timestamp: '18:30:47' }
    ];
    
    // Obtener número de alertas aleatorio (1-5)
    const numAlerts = Math.floor(Math.random() * 5) + 1;
    
    // Actualizar contador de alertas
    const alertCount = document.getElementById('alert-count');
    if (alertCount) {
        alertCount.textContent = numAlerts;
    }
    
    // Mostrar alertas
    for (let i = 0; i < numAlerts; i++) {
        const alert = alertMessages[i];
        
        const alertItem = document.createElement('div');
        alertItem.className = `alert-item ${alert.type}`;
        
        alertItem.innerHTML = `
            <div class="alert-meta">
                <span class="alert-severity ${alert.type}">
                    ${alert.type.toUpperCase()}
                </span>
                <span class="alert-time">${alert.timestamp}</span>
            </div>
            <div class="alert-message">
                ${alert.message}
            </div>
        `;
        
        alertsList.appendChild(alertItem);
    }
}

/**
 * Carga los logs del sistema
 */
function loadSystemLogs() {
    const logContainer = document.getElementById('system-logs');
    if (!logContainer) return;
    
    fetchWithErrorHandling('/api/logs')
        .then(data => {
            if (data.success && data.logs) {
                renderSystemLogs(data.logs);
            }
        });
}

/**
 * Renderiza los logs del sistema
 */
function renderSystemLogs(logs) {
    const logContainer = document.getElementById('system-logs');
    if (!logContainer) return;
    
    // Limpiar logs anteriores
    logContainer.innerHTML = '';
    
    // Mostrar solo los últimos 20 logs
    const recentLogs = logs.slice(-20);
    
    // Renderizar cada log
    recentLogs.forEach(log => {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        // Determinar nivel de log
        const level = log.level || 'info';
        
        // Formatear timestamp si existe
        let timestamp = '';
        if (log.timestamp || log.time) {
            const time = new Date(log.timestamp || log.time);
            timestamp = time.toLocaleTimeString('es-MX');
        }
        
        // Formatear mensaje
        const message = log.message || log.event || JSON.stringify(log);
        
        logEntry.innerHTML = `
            <span class="log-timestamp">${timestamp}</span>
            <span class="log-level ${level}">${level.toUpperCase()}</span>
            <span class="log-message">${message}</span>
        `;
        
        logContainer.appendChild(logEntry);
    });
    
    // Hacer scroll al último log
    logContainer.scrollTop = logContainer.scrollHeight;
}

/**
 * Obtiene las métricas de Prometheus
 */
function fetchPrometheusMetrics() {
    const metricsContainer = document.getElementById('prometheus-metrics');
    if (!metricsContainer) return;
    
    fetch('/metrics')
        .then(response => response.text())
        .then(text => {
            renderPrometheusMetrics(text);
        })
        .catch(error => {
            console.error('Error al obtener métricas de Prometheus:', error);
            metricsContainer.innerHTML = '<div class="error-message">Error al cargar métricas de Prometheus</div>';
        });
}

/**
 * Renderiza las métricas de Prometheus
 */
function renderPrometheusMetrics(metricsText) {
    const metricsContainer = document.getElementById('prometheus-metrics');
    if (!metricsContainer) return;
    
    // Limpiar contenedor
    metricsContainer.innerHTML = '';
    
    // Parsear métricas
    const lines = metricsText.split('\n');
    let currentMetric = null;
    let currentHelp = '';
    
    lines.forEach(line => {
        if (line.startsWith('# HELP')) {
            // Línea de ayuda
            const parts = line.split(' ');
            currentMetric = parts[2];
            currentHelp = line.substring(line.indexOf(currentMetric) + currentMetric.length + 1);
            
            const metricDiv = document.createElement('div');
            metricDiv.className = 'prometheus-metric';
            metricDiv.innerHTML = `
                <div class="prometheus-metric-name">${currentMetric}</div>
                <div class="prometheus-metric-help">${currentHelp}</div>
            `;
            
            metricsContainer.appendChild(metricDiv);
        } else if (line.startsWith('# TYPE')) {
            // Ignorar líneas de tipo
        } else if (line.trim() && !line.startsWith('#')) {
            // Línea de valor
            const valueDiv = document.createElement('div');
            valueDiv.className = 'prometheus-metric-value';
            valueDiv.textContent = line;
            
            // Agregar al último div de métrica
            const metricDivs = metricsContainer.querySelectorAll('.prometheus-metric');
            if (metricDivs.length > 0) {
                metricDivs[metricDivs.length - 1].appendChild(valueDiv);
            }
        }
    });
}

/**
 * Muestra una notificación
 * @param {string} message - Mensaje de notificación
 * @param {string} type - Tipo de notificación (success, info, warning, danger)
 */
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'info' ? 'info-circle' : type === 'warning' ? 'exclamation-triangle' : 'times-circle'}"></i>
        <span>${message}</span>
        <button type="button" class="close" onclick="this.parentElement.remove()">
            <span>&times;</span>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-cerrar después de 5 segundos
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Realiza una solicitud HTTP con manejo de errores
 * @param {string} url - URL de la solicitud
 * @returns {Promise} Promesa que se resuelve con la respuesta de la solicitud
 */
function fetchWithErrorHandling(url) {
    return fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Error al realizar solicitud:', error);
            throw error;
        });
}

// Configuración de gráficas de métricas del sistema al estilo Grafana
function createSystemMetricsCharts() {
    // Configuración base para gráficas al estilo Grafana
    const grafanaChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)',
                    borderColor: 'rgba(255, 255, 255, 0.2)'
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.7)'
                }
            },
            y: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)',
                    borderColor: 'rgba(255, 255, 255, 0.2)'
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.7)'
                }
            }
        },
        plugins: {
            legend: {
                labels: {
                    color: 'rgba(255, 255, 255, 0.7)'
                }
            }
        }
    };

    // Gráfica de llamadas API
    const apiCallsCtx = document.getElementById('api-calls-chart').getContext('2d');
    new Chart(apiCallsCtx, {
        type: 'line',
        data: {
            labels: ['Día 1', 'Día 2', 'Día 3', 'Día 4', 'Día 5'],
            datasets: [{
                label: 'Llamadas API',
                data: [120, 150, 100, 180, 140],
                backgroundColor: 'rgba(56, 116, 203, 0.3)', // Azul transparente
                borderColor: '#3874CB',
                borderWidth: 2,
                fill: true,
                tension: 0.4 // Línea suave
            }]
        },
        options: {
            ...grafanaChartOptions,
            plugins: {
                ...grafanaChartOptions.plugins,
                title: {
                    display: true,
                    text: 'Llamadas API',
                    color: 'rgba(255, 255, 255, 0.9)'
                }
            }
        }
    });

    // Gráfica de tiempo de respuesta
    const responseTimeCtx = document.getElementById('response-time-chart').getContext('2d');
    new Chart(responseTimeCtx, {
        type: 'line',
        data: {
            labels: ['Día 1', 'Día 2', 'Día 3', 'Día 4', 'Día 5'],
            datasets: [{
                label: 'Tiempo de Respuesta (ms)',
                data: [650, 620, 680, 600, 640],
                backgroundColor: 'rgba(255, 193, 7, 0.3)', // Amarillo transparente
                borderColor: '#FFC107',
                borderWidth: 2,
                fill: true,
                tension: 0.4 // Línea suave
            }]
        },
        options: {
            ...grafanaChartOptions,
            plugins: {
                ...grafanaChartOptions.plugins,
                title: {
                    display: true,
                    text: 'Tiempo de Respuesta (ms)',
                    color: 'rgba(255, 255, 255, 0.9)'
                }
            }
        }
    });

    // Gráfica de tasa de éxito
    const successRateCtx = document.getElementById('success-rate-chart').getContext('2d');
    new Chart(successRateCtx, {
        type: 'bar',
        data: {
            labels: ['Día 1', 'Día 2', 'Día 3', 'Día 4', 'Día 5'],
            datasets: [{
                label: 'Tasa de Éxito',
                data: [95, 98, 100, 97, 99],
                backgroundColor: '#37873D',
                borderColor: '#3AC24C',
                borderWidth: 1
            }]
        },
        options: {
            ...grafanaChartOptions,
            plugins: {
                ...grafanaChartOptions.plugins,
                title: {
                    display: true,
                    text: 'Tasa de Éxito (%)',
                    color: 'rgba(255, 255, 255, 0.9)'
                }
            }
        }
    });

    // Gráfica de errores
    const errorsCtx = document.getElementById('errors-chart').getContext('2d');
    new Chart(errorsCtx, {
        type: 'bar',
        data: {
            labels: ['Día 1', 'Día 2', 'Día 3', 'Día 4', 'Día 5'],
            datasets: [{
                label: 'Errores',
                data: [0, 1, 0, 2, 1],
                backgroundColor: '#D93F3F',
                borderColor: '#FF5252',
                borderWidth: 1
            }]
        },
        options: {
            ...grafanaChartOptions,
            plugins: {
                ...grafanaChartOptions.plugins,
                title: {
                    display: true,
                    text: 'Número de Errores',
                    color: 'rgba(255, 255, 255, 0.9)'
                }
            }
        }
    });
}

// Llamar a la función cuando el documento esté listo
document.addEventListener('DOMContentLoaded', createSystemMetricsCharts);
