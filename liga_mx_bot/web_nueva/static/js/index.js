/**
 * Liga MX Bot - Página Principal
 * 
 * Script específico para la página principal que muestra
 * los partidos de Liga MX y la información del sistema.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar la página principal
    loadMatches();
    loadSystemMetrics();
    updateCurrentTime();
    
    // Configurar actualizaciones periódicas
    setInterval(loadMatches, 60000); // Actualizar partidos cada minuto
    setInterval(loadSystemMetrics, 30000); // Actualizar métricas cada 30 segundos
    setInterval(updateCurrentTime, 1000); // Actualizar reloj cada segundo
    
    // Evento para botón de actualizar
    document.getElementById('refresh-matches').addEventListener('click', function() {
        loadMatches();
        loadSystemMetrics();
    });
});

/**
 * Carga los partidos de Liga MX desde la API
 */
function loadMatches() {
    const matchesList = document.getElementById('matches-list');
    const loadingIndicator = matchesList.querySelector('.loading');
    
    // Mostrar indicador de carga
    if (loadingIndicator) {
        loadingIndicator.style.display = 'flex';
    }
    
    // Registro para depuración
    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Solicitando datos de partidos...`);
    
    fetch('/api/matches')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Ocultar indicador de carga
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
            
            if (data.success && data.matches && data.matches.length > 0) {
                // Limpiar contenedor
                matchesList.innerHTML = '';
                
                // Renderizar partidos
                renderMatches(data.matches);
                console.log(`[${new Date().toLocaleTimeString('es-MX')}] Se cargaron ${data.matches.length} partidos correctamente.`);
                
                // Actualizar logs
                addLog('INFO', `Datos de partidos actualizados. ${data.matches.length} partidos cargados.`);
            } else {
                // No hay partidos disponibles
                matchesList.innerHTML = `
                    <div class="no-matches">
                        <i class="fas fa-info-circle"></i>
                        <p>No hay partidos disponibles en este momento.</p>
                    </div>
                `;
                
                console.warn(`[${new Date().toLocaleTimeString('es-MX')}] No se encontraron partidos: ${data.error || 'Sin datos'}`);
                addLog('WARNING', 'No se encontraron partidos disponibles.');
            }
        })
        .catch(error => {
            // Mostrar error
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
            
            matchesList.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error al cargar los partidos.</p>
                    <button class="retry-btn" onclick="loadMatches()">
                        <i class="fas fa-sync-alt"></i> Intentar de nuevo
                    </button>
                </div>
            `;
            
            console.error(`[${new Date().toLocaleTimeString('es-MX')}] Error al cargar partidos:`, error);
            addLog('ERROR', `Error al cargar partidos: ${error.message}`);
        });
}

/**
 * Renderiza los partidos agrupados por fecha
 * @param {Array} matches - Lista de partidos
 */
function renderMatches(matches) {
    const matchesList = document.getElementById('matches-list');
    
    // Agrupar partidos por fecha
    const matchesByDate = {};
    
    matches.forEach(match => {
        const date = match.date;
        if (!matchesByDate[date]) {
            matchesByDate[date] = [];
        }
        matchesByDate[date].push(match);
    });
    
    // Ordenar fechas
    const sortedDates = Object.keys(matchesByDate).sort();
    
    // Renderizar partidos por fecha
    sortedDates.forEach(date => {
        const dateMatches = matchesByDate[date];
        
        // Crear contenedor para esta fecha
        const dateSection = document.createElement('div');
        dateSection.className = 'matches-date-section';
        
        // Crear encabezado de fecha
        const dateHeader = document.createElement('h3');
        dateHeader.className = 'date-header';
        dateHeader.textContent = formatDate(date);
        dateSection.appendChild(dateHeader);
        
        // Crear contenedor para los partidos de esta fecha
        const matchesContainer = document.createElement('div');
        matchesContainer.className = 'date-matches';
        
        // Ordenar partidos por hora
        dateMatches.sort((a, b) => {
            const timeA = a.time ? a.time.split(':').map(Number) : [0, 0];
            const timeB = b.time ? b.time.split(':').map(Number) : [0, 0];
            
            // Comparar horas primero, luego minutos
            if (timeA[0] !== timeB[0]) {
                return timeA[0] - timeB[0];
            }
            return timeA[1] - timeB[1];
        });
        
        // Añadir cada partido
        dateMatches.forEach(match => {
            const matchCard = createMatchCard(match);
            matchesContainer.appendChild(matchCard);
        });
        
        dateSection.appendChild(matchesContainer);
        matchesList.appendChild(dateSection);
    });
}

/**
 * Crea una tarjeta HTML para un partido
 * @param {Object} match - Datos del partido
 * @returns {HTMLElement} - Elemento DOM de la tarjeta
 */
function createMatchCard(match) {
    const matchCard = document.createElement('div');
    matchCard.className = 'match-card';
    
    // Determinar el estado del partido
    let statusClass = 'not-started';
    let statusText = 'No iniciado';
    
    if (match.status === 'In Play' || match.status === 'En juego') {
        statusClass = 'in-play';
        statusText = 'En juego';
    } else if (match.status === 'Finished' || match.status === 'Finalizado') {
        statusClass = 'finished';
        statusText = 'Finalizado';
    }
    
    // Formatear hora (ya está en UTC-6 desde la API)
    const formattedTime = formatTime(match.time);
    
    // Construir HTML
    matchCard.innerHTML = `
        <div class="match-header">
            <div class="match-competition">${match.competition || 'Liga MX'}</div>
            <div class="match-status ${statusClass}">${statusText}</div>
        </div>
        <div class="match-content">
            <div class="team home-team">
                <img src="${match.homeTeam.logo || getDefaultLogo()}" alt="${match.homeTeam.name}" class="team-logo">
                <div class="team-name">${match.homeTeam.name}</div>
                <div class="team-score">${match.homeTeam.score !== undefined ? match.homeTeam.score : '-'}</div>
            </div>
            <div class="match-info">
                <div class="match-time">${formattedTime}</div>
                <div class="match-venue">${match.venue || 'Estadio no especificado'}</div>
            </div>
            <div class="team away-team">
                <img src="${match.awayTeam.logo || getDefaultLogo()}" alt="${match.awayTeam.name}" class="team-logo">
                <div class="team-name">${match.awayTeam.name}</div>
                <div class="team-score">${match.awayTeam.score !== undefined ? match.awayTeam.score : '-'}</div>
            </div>
        </div>
    `;
    
    return matchCard;
}

/**
 * Formatea una fecha en formato legible en español
 * @param {string} dateString - Fecha en formato ISO
 * @returns {string} - Fecha formateada en español
 */
function formatDate(dateString) {
    const days = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    const months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    
    const date = new Date(dateString);
    
    // Ajustar a UTC-6 (hora de México)
    const mexicoDate = new Date(date.getTime() - 6 * 60 * 60 * 1000);
    
    const dayName = days[mexicoDate.getUTCDay()];
    const day = mexicoDate.getUTCDate();
    const month = months[mexicoDate.getUTCMonth()];
    
    return `${dayName}, ${day} de ${month}`;
}

/**
 * Formatea una hora en formato de 12 horas con AM/PM
 * @param {string} timeString - Hora en formato HH:MM
 * @returns {string} - Hora formateada en 12h con AM/PM
 */
function formatTime(timeString) {
    if (!timeString) return 'Hora por confirmar';
    
    const [hours, minutes] = timeString.split(':').map(Number);
    
    // Determinar AM/PM
    const period = hours >= 12 ? 'p.m.' : 'a.m.';
    
    // Convertir a formato 12 horas
    const hours12 = hours % 12 || 12;
    
    // Formatear la hora
    return `${hours12}:${minutes.toString().padStart(2, '0')} ${period}`;
}

/**
 * Obtiene un logo predeterminado en caso de que no exista el del equipo
 * @returns {string} - URL del logo predeterminado
 */
function getDefaultLogo() {
    return '/static/img/ligamx/default-team.png';
}

/**
 * Carga y actualiza las métricas del sistema
 */
function loadSystemMetrics() {
    fetch('/api/metrics_data')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.metrics) {
                // Actualizar contadores
                document.getElementById('api-calls').textContent = data.metrics.api_calls?.total || 0;
                document.getElementById('response-time').textContent = data.metrics.api_calls?.avg_response_time ?
                    `${(data.metrics.api_calls.avg_response_time * 1000).toFixed(0)}ms` : '0ms';
                document.getElementById('api-errors').textContent = data.metrics.errors?.total || 0;
                
                // Actualizar estado del sistema
                const systemStatus = document.getElementById('system-status');
                const systemStatusText = document.getElementById('system-status-text');
                
                if (data.metrics.status === 'online') {
                    systemStatus.className = 'status-indicator online';
                    systemStatusText.textContent = 'En línea';
                } else if (data.metrics.status === 'warning') {
                    systemStatus.className = 'status-indicator warning';
                    systemStatusText.textContent = 'Advertencia';
                } else if (data.metrics.status === 'offline') {
                    systemStatus.className = 'status-indicator offline';
                    systemStatusText.textContent = 'Fuera de línea';
                }
                
                console.log(`[${new Date().toLocaleTimeString('es-MX')}] Métricas del sistema actualizadas.`);
            }
        })
        .catch(error => {
            console.error(`[${new Date().toLocaleTimeString('es-MX')}] Error al cargar métricas:`, error);
        });
}

/**
 * Añade un registro de log a la interfaz
 * @param {string} level - Nivel del log (INFO, WARNING, ERROR)
 * @param {string} message - Mensaje del log
 */
function addLog(level, message) {
    const logsContainer = document.getElementById('recent-logs');
    const timestamp = new Date().toLocaleTimeString('es-MX');
    
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    logEntry.innerHTML = `
        <span class="log-time">${timestamp}</span>
        <span class="log-level ${level.toLowerCase()}">${level}</span>
        <span class="log-message">${message}</span>
    `;
    
    // Agregar al principio para que los más recientes estén arriba
    logsContainer.insertBefore(logEntry, logsContainer.firstChild);
    
    // Limitar a 10 logs
    if (logsContainer.children.length > 10) {
        logsContainer.removeChild(logsContainer.lastChild);
    }
}

/**
 * Actualiza la hora actual en el footer
 */
function updateCurrentTime() {
    const currentTime = document.getElementById('current-time');
    if (currentTime) {
        const now = new Date();
        const options = { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit',
            hour12: true,
            timeZone: 'America/Mexico_City'
        };
        currentTime.textContent = `Hora actual: ${now.toLocaleTimeString('es-MX', options)}`;
    }
}
