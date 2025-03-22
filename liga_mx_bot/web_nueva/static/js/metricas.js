/**
 * Liga MX Bot - Métricas y Estadísticas
 * 
 * Script específico para la página de métricas y estadísticas
 * de Liga MX, incluyendo tabla de posiciones y estadísticas de jugadores.
 */

// Configuración global
const CURRENT_SEASON = 'Clausura 2025';
const CHART_COLORS = [
    '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', 
    '#f95d6a', '#ff7c43', '#ffa600', '#00876c', '#439981',
    '#6aaa96', '#8cbcac', '#aed0c3', '#f1f1f1'
];

// Caché de datos para mejorar el rendimiento
const statsCache = {
    data: null,
    timestamp: null,
    season: null,
    expirationTime: 5 * 60 * 1000 // 5 minutos en milisegundos
};

// Inicializar la página cuando el documento esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Inicializando página de métricas...`);
    
    // Inicializar la página de métricas
    initMetricsPage();
    
    // Configurar botones de filtrado
    setupFilterButtons();
    
    // Configurar botón de actualización
    const refreshButton = document.getElementById('refresh-data');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            console.log(`[${new Date().toLocaleTimeString('es-MX')}] Actualizando datos...`);
            refreshAllStats();
        });
    }
    
    // Actualizar automáticamente cada 5 minutos
    // Para depuración, comentar esta línea si causa problemas
    setInterval(refreshAllStats, 300000);
    
    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Página inicializada correctamente`);
});

/**
 * Inicializa la página de métricas
 */
function initMetricsPage() {
    showLoading();
    
    // Cargar estadísticas iniciales
    loadAndRenderStats();
    
    // Actualizar temporada actual
    const currentSeasonEl = document.getElementById('current-season');
    if (currentSeasonEl) {
        currentSeasonEl.textContent = CURRENT_SEASON;
    }
}

/**
 * Comprueba si los datos en caché son válidos
 * @returns {boolean} true si los datos son válidos
 */
function isCacheValid() {
    if (!statsCache.data || !statsCache.timestamp) {
        return false;
    }
    
    const now = new Date().getTime();
    const cacheAge = now - statsCache.timestamp;
    return cacheAge < statsCache.expirationTime;
}

/**
 * Realiza una petición fetch con manejo de errores
 * @param {string} url - URL a consultar
 * @returns {Promise} Promesa con la respuesta en formato JSON
 */
function fetchWithErrorHandling(url) {
    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Solicitando datos de: ${url}`);
    
    return fetch(url)
        .then(response => {
            console.log(`[${new Date().toLocaleTimeString('es-MX')}] Respuesta recibida de ${url}:`, response.status);
            
            if (!response.ok) {
                console.error(`[ERROR] ${new Date().toLocaleTimeString('es-MX')}] Error HTTP: ${response.status} al consultar ${url}`);
                throw new Error(`Error HTTP: ${response.status}`);
            }
            
            return response.json()
                .then(data => {
                    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Datos JSON recibidos de ${url}:`, data);
                    
                    // Verificar si la respuesta tiene formato adecuado
                    if (!data) {
                        throw new Error('Respuesta vacía del servidor');
                    }
                    
                    return data;
                })
                .catch(err => {
                    console.error(`[ERROR] ${new Date().toLocaleTimeString('es-MX')}] Error al procesar JSON de ${url}:`, err);
                    throw new Error(`Error al procesar respuesta: ${err.message}`);
                });
        })
        .catch(error => {
            console.error(`[ERROR] ${new Date().toLocaleTimeString('es-MX')}] Error en la solicitud a ${url}:`, error);
            showError(`Error al cargar datos: ${error.message}`);
            throw error;
        });
}

// Mapeo de nombres de equipos a IDs para logos
const TEAM_LOGO_MAP = {
    'América': 'america',
    'Atlas': 'atlas',
    'Atlético San Luis': 'sanluis',
    'Cruz Azul': 'cruzazul',
    'FC Juárez': 'juarez',
    'Juárez': 'juarez',
    'Juarez': 'juarez',
    'Guadalajara': 'guadalajara',
    'León': 'leon',
    'Mazatlán FC': 'mazatlan',
    'Mazatlán': 'mazatlan',
    'Mazatlan FC': 'mazatlan',
    'Mazatlan': 'mazatlan',
    'Monterrey': 'monterrey',
    'Necaxa': 'necaxa',
    'Pachuca': 'pachuca',
    'Puebla': 'puebla',
    'Pumas UNAM': 'pumas',
    'Pumas': 'pumas',
    'Querétaro': 'queretaro',
    'Santos Laguna': 'santos',
    'Santos': 'santos',
    'Tijuana': 'tijuana',
    'Toluca': 'toluca',
    'UANL': 'tigres',
    'Tigres': 'tigres',
    'Tigres UANL': 'tigres'
};

// Referencias a gráficos
let standingsTable = null;
let goalscorersChart = null;
let cardsChart = null;
let foulsChart = null;
let teamStatsChart = null;

/**
 * Configura los botones de filtrado para las estadísticas
 */
function setupFilterButtons() {
    // Filtradores de temporada
    const seasonFilters = document.querySelectorAll('.season-filter');
    seasonFilters.forEach(button => {
        button.addEventListener('click', function() {
            // Remover clase activa de todos los botones
            seasonFilters.forEach(btn => btn.classList.remove('active'));
            
            // Agregar clase activa al botón clickeado
            this.classList.add('active');
            
            // Actualizar temporada seleccionada
            const selectedSeason = this.dataset.season;
            
            // Actualizar estadísticas con la temporada seleccionada
            refreshAllStats(selectedSeason);
        });
    });
    
    // Filtradores de estadísticas de equipo
    const teamStatFilters = document.querySelectorAll('.team-stat-filter');
    teamStatFilters.forEach(button => {
        button.addEventListener('click', function() {
            // Remover clase activa de todos los botones
            teamStatFilters.forEach(btn => btn.classList.remove('active'));
            
            // Agregar clase activa al botón clickeado
            this.classList.add('active');
            
            // Actualizar estadística seleccionada
            const selectedStat = this.dataset.stat;
            
            // Actualizar gráfico con la estadística seleccionada
            updateTeamStatsChart(selectedStat);
        });
    });
}

/**
 * Muestra el indicador de carga
 */
function showLoading() {
    const loadingIndicators = document.querySelectorAll('.loading-indicator');
    loadingIndicators.forEach(indicator => {
        indicator.style.display = 'flex';
    });
}

/**
 * Oculta el indicador de carga
 */
function hideLoading() {
    const loadingIndicators = document.querySelectorAll('.loading-indicator');
    loadingIndicators.forEach(indicator => {
        indicator.style.display = 'none';
    });
    
    // También ocultar mensaje de estado si existe
    const statusMsg = document.getElementById('loading-status-message');
    if (statusMsg) statusMsg.remove();
}

/**
 * Actualiza todas las estadísticas
 * @param {string} season - Temporada seleccionada (opcional)
 */
function refreshAllStats(season = CURRENT_SEASON) {
    showLoading();
    loadAndRenderStats(season);
    
    // Registro para depuración
    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Actualizando estadísticas para la temporada: ${season}`);
}

/**
 * Carga y renderiza todas las estadísticas
 * @param {string} season - Temporada seleccionada
 */
function loadAndRenderStats(season = CURRENT_SEASON) {
    // Mostrar indicadores de carga para todas las secciones
    showLoading();
    
    // Comprobar si tenemos datos en caché válidos
    if (isCacheValid() && statsCache.season === season) {
        console.log(`[${new Date().toLocaleTimeString('es-MX')}] Usando datos en caché para ${season}`);
        renderAllStats(statsCache.data);
        return;
    }
    
    // Registro para depuración
    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Solicitando datos de estadísticas para ${season}...`);
    
    // Mostrar un mensaje al usuario
    const statusMessage = document.createElement('div');
    statusMessage.id = 'loading-status-message';
    statusMessage.className = 'loading-status';
    statusMessage.textContent = 'Cargando datos de estadísticas...';
    document.querySelector('.metrics-container').prepend(statusMessage);
    
    // Obtener datos de la API con la temporada seleccionada
    fetchWithErrorHandling(`/api/stats?season=${encodeURIComponent(season)}`)
        .then(response => {
            // Eliminar mensaje de estado
            const statusMsg = document.getElementById('loading-status-message');
            if (statusMsg) statusMsg.remove();
            
            if (response.success) {
                console.log(`[${new Date().toLocaleTimeString('es-MX')}] Datos de estadísticas cargados correctamente.`);
                
                // Guardar en caché
                statsCache.data = response.data;
                statsCache.timestamp = new Date().getTime();
                statsCache.season = season;
                
                // Renderizar todos los datos
                renderAllStats(response.data);
            } else {
                hideLoading();
                showError(`Error al cargar estadísticas: ${response.error || 'Error desconocido'}`);
                console.error(`[ERROR] ${new Date().toLocaleTimeString('es-MX')} Error al cargar estadísticas:`, response.error);
            }
        })
        .catch(error => {
            // Eliminar mensaje de estado
            const statusMsg = document.getElementById('loading-status-message');
            if (statusMsg) statusMsg.remove();
            
            hideLoading();
            showError(`Error al cargar estadísticas: ${error}`);
            console.error(`[ERROR] ${new Date().toLocaleTimeString('es-MX')} Error al cargar estadísticas:`, error);
        });
}

/**
 * Renderiza todos los datos estadísticos de forma paralela
 * @param {Object} stats - Datos estadísticos
 */
function renderAllStats(stats) {
    if (!stats) {
        hideLoading();
        showError('No se recibieron datos estadísticos válidos');
        return;
    }
    
    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Renderizando datos estadísticos:`, stats);
    
    // Usar Promise.all para paralelizar el renderizado
    const renderPromises = [
        // Función que renderiza la tabla de posiciones
        () => renderStandings(stats.standings || []),
        // Función que renderiza los goleadores
        () => renderGoalscorers(stats.top_scorers || []),
        // Función que renderiza las tarjetas
        () => renderCards(stats.cards || {}),
        // Función que renderiza las faltas
        () => renderFouls(stats.fouls || []),
        // Función que renderiza las estadísticas de equipos
        () => {
            // Almacenar estadísticas de equipos para uso posterior
            if (stats.metrics && Array.isArray(stats.metrics.teams)) {
                storeTeamStats(stats.metrics.teams);
                renderTeamStats(stats.metrics.teams);
            }
        }
    ];
    
    // Ejecutar todas las promesas
    Promise.all(renderPromises.map(fn => {
        try {
            return Promise.resolve(fn());
        } catch (error) {
            console.error(`[ERROR] ${new Date().toLocaleTimeString('es-MX')}] Error en renderizado:`, error);
            return Promise.resolve(null);
        }
    }))
    .then(() => {
        // Ocultar indicadores de carga
        hideLoading();
        
        // Actualizar timestamp de última actualización
        updateLastUpdateTimestamp();
        
        // Cargar métricas del sistema
        loadSystemMetrics();
    });
}

/**
 * Actualiza la marca de tiempo de última actualización
 */
function updateLastUpdateTimestamp() {
    const lastUpdateEl = document.getElementById('last-update');
    if (lastUpdateEl) {
        const lastUpdate = new Date();
        const options = { 
            dateStyle: 'medium', 
            timeStyle: 'short', 
            timeZone: 'America/Mexico_City'
        };
        lastUpdateEl.textContent = 
            `Última actualización: ${lastUpdate.toLocaleString('es-MX', options)}`;
    }
}

/**
 * Muestra un mensaje de error
 * @param {string} message - Mensaje de error
 */
function showError(message) {
    const errorContainers = document.querySelectorAll('.error-message');
    errorContainers.forEach(container => {
        container.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <p>${message}</p>
            <button onclick="refreshAllStats()" class="retry-button">
                <i class="fas fa-sync-alt"></i> Intentar de nuevo
            </button>
        `;
        container.style.display = 'flex';
    });
}

/**
 * Obtiene la URL del logo de un equipo
 * @param {string} teamName - Nombre del equipo
 * @returns {string} URL del logo
 */
function getTeamLogo(teamName) {
    const teamId = TEAM_LOGO_MAP[teamName] || 'default';
    return `/static/img/ligamx/${teamId}.png`;
}

/**
 * Inicializa la tabla de posiciones
 */
function updateStandings(standings) {
    const standingsTable = document.getElementById('standings-table');
    if (!standingsTable || !standings || !standings.length) return;
    
    // Limpiar tabla actual
    const tableBody = standingsTable.querySelector('tbody');
    if (tableBody) {
        tableBody.innerHTML = '';
        
        // Agregar filas para cada equipo
        standings.forEach((team, index) => {
            const row = document.createElement('tr');
            
            // Formatear fila de la tabla
            row.innerHTML = `
                <td>${index + 1}</td>
                <td class="team-cell">
                    <img src="${getTeamLogoUrl(team.team)}" alt="${team.team}" class="team-logo-small">
                    <span>${team.team}</span>
                </td>
                <td>${team.played || 0}</td>
                <td>${team.won || 0}</td>
                <td>${team.drawn || 0}</td>
                <td>${team.lost || 0}</td>
                <td>${team.goalsFor || 0}</td>
                <td>${team.goalsAgainst || 0}</td>
                <td>${team.goalDifference || 0}</td>
                <td class="points">${team.points || 0}</td>
            `;
            
            tableBody.appendChild(row);
        });
    }
}

/**
 * Actualiza la tabla de goleadores
 */
function updateTopScorers(scorers) {
    const scorersTable = document.getElementById('scorers-table');
    if (!scorersTable || !scorers || !scorers.length) return;
    
    // Limpiar tabla actual
    const tableBody = scorersTable.querySelector('tbody');
    if (tableBody) {
        tableBody.innerHTML = '';
        
        // Agregar filas para cada goleador
        scorers.forEach((player, index) => {
            const row = document.createElement('tr');
            
            // Formatear fila de la tabla
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${player.name}</td>
                <td class="team-cell">
                    <img src="${getTeamLogoUrl(player.team)}" alt="${player.team}" class="team-logo-small">
                    <span>${player.team}</span>
                </td>
                <td class="goals">${player.goals}</td>
                <td>${player.penalties || 0}</td>
                <td>${player.appearances || '-'}</td>
            `;
            
            tableBody.appendChild(row);
        });
    }
}

/**
 * Actualiza las estadísticas de equipos
 */
function updateTeamStats(teamStats) {
    // Aquí actualizaríamos elementos como:
    // - Equipo con más goles
    // - Equipo con mejor defensa
    // - Equipo con más tarjetas, etc.
    
    if (!teamStats) return;
    
    // Actualizar estadísticas generales si existen
    if (document.getElementById('most-goals-team')) {
        const mostGoalsTeam = teamStats.mostGoals || { team: 'No disponible', value: 0 };
        document.getElementById('most-goals-team').textContent = mostGoalsTeam.team;
        document.getElementById('most-goals-value').textContent = mostGoalsTeam.value;
    }
    
    if (document.getElementById('best-defense-team')) {
        const bestDefenseTeam = teamStats.bestDefense || { team: 'No disponible', value: 0 };
        document.getElementById('best-defense-team').textContent = bestDefenseTeam.team;
        document.getElementById('best-defense-value').textContent = bestDefenseTeam.value;
    }
    
    if (document.getElementById('most-cards-team')) {
        const mostCardsTeam = teamStats.mostCards || { team: 'No disponible', value: 0 };
        document.getElementById('most-cards-team').textContent = mostCardsTeam.team;
        document.getElementById('most-cards-value').textContent = mostCardsTeam.value;
    }
}

/**
 * Inicializa los gráficos con los datos
 */
function initCharts(data) {
    // Gráfico de goles por equipo
    initGoalsChart(data.teamStats?.goalsData);
    
    // Gráfico de tarjetas
    initCardsChart(data.teamStats?.cardsData);
}

/**
 * Inicializa el gráfico de goles por equipo
 */
function initGoalsChart(goalsData) {
    const chartCanvas = document.getElementById('goals-chart');
    if (!chartCanvas || !goalsData) return;
    
    // Destruir gráfico existente si hay uno
    if (window.goalsChart) {
        window.goalsChart.destroy();
    }
    
    // Preparar datos para el gráfico
    const teams = goalsData.map(item => item.team);
    const goalsFor = goalsData.map(item => item.goalsFor);
    const goalsAgainst = goalsData.map(item => item.goalsAgainst);
    
    // Crear nuevo gráfico
    window.goalsChart = new Chart(chartCanvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: teams,
            datasets: [
                {
                    label: 'Goles a Favor',
                    data: goalsFor,
                    backgroundColor: 'rgba(0, 169, 79, 0.7)',
                    borderColor: 'rgba(0, 169, 79, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Goles en Contra',
                    data: goalsAgainst,
                    backgroundColor: 'rgba(216, 35, 42, 0.7)',
                    borderColor: 'rgba(216, 35, 42, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Goles por Equipo'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Goles'
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

/**
 * Inicializa el gráfico de tarjetas
 */
function initCardsChart(cardsData) {
    const chartCanvas = document.getElementById('cards-chart');
    if (!chartCanvas || !cardsData) return;
    
    // Destruir gráfico existente si hay uno
    if (window.cardsChart) {
        window.cardsChart.destroy();
    }
    
    // Preparar datos para el gráfico
    const teams = cardsData.map(item => item.team);
    const yellowCards = cardsData.map(item => item.yellowCards);
    const redCards = cardsData.map(item => item.redCards);
    
    // Crear nuevo gráfico
    window.cardsChart = new Chart(chartCanvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: teams,
            datasets: [
                {
                    label: 'Tarjetas Amarillas',
                    data: yellowCards,
                    backgroundColor: 'rgba(255, 193, 7, 0.8)',
                    borderColor: 'rgba(255, 193, 7, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Tarjetas Rojas',
                    data: redCards,
                    backgroundColor: 'rgba(220, 53, 69, 0.8)',
                    borderColor: 'rgba(220, 53, 69, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Tarjetas por Equipo'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const dataset = context.dataset.label;
                            const value = context.raw;
                            return `${dataset}: ${value}`;
                        }
                    }
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Cantidad'
                    },
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

/**
 * Muestra un mensaje de error en la página
 */
function showError(message) {
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.textContent = message;
    
    // Agregar al contenedor principal
    const container = document.querySelector('.metrics-container');
    if (container) {
        // Eliminar errores anteriores
        const existingErrors = container.querySelectorAll('.error-message');
        existingErrors.forEach(el => el.remove());
        
        // Agregar nuevo error al inicio
        container.insertBefore(errorElement, container.firstChild);
    }
}

/**
 * Carga los datos de estadísticas desde la API
 * @param {string} season - Temporada (Clausura2025, Apertura2024, etc.)
 */
function loadStatsData(season = 'Clausura2025') {
    // Mostrar indicadores de carga
    showLoading();
    
    // Obtener datos de la API
    fetchWithErrorHandling(`/api/stats?season=${season}`)
        .then(data => {
            if (data.success) {
                // Actualizar la interfaz con los nuevos datos
                updateStatsUI(data);
            } else {
                showError('Error al cargar datos de estadísticas');
            }
        })
        .catch(error => {
            showError(`Error: ${error.message}`);
        })
        .finally(() => {
            // Ocultar indicadores de carga
            hideLoading();
        });
}

/**
 * Actualiza la interfaz con los datos de estadísticas
 */
function updateStatsUI(data) {
    // Usar la función renderAllStats para procesar los datos
    // Esto evita duplicación de código y asegura consistencia
    renderAllStats(data);
}

/**
 * Renderiza la tabla de posiciones
 * @param {Array} standings - Datos de la tabla de posiciones
 */
function renderStandings(standings) {
    // Corregir el selector para que use el ID correcto definido en el HTML
    const standingsTableBody = document.querySelector('#standings-body');
    
    if (!standingsTableBody || !standings || standings.length === 0) {
        console.warn(`[${new Date().toLocaleTimeString('es-MX')}] No hay datos de posiciones disponibles`);
        return;
    }
    
    // Obtener el contenedor para mostrarlo
    const standingsContainer = document.getElementById('standings-container');
    if (standingsContainer) {
        standingsContainer.style.display = 'block';
    }
    
    // Ocultar indicador de carga
    const loadingIndicator = document.getElementById('standings-loading');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
    
    // Limpiar tabla
    standingsTableBody.innerHTML = '';
    
    // Ordenar por puntos (descendente)
    const sortedStandings = [...standings].sort((a, b) => {
        // Primero por puntos
        if (b.points !== a.points) {
            return b.points - a.points;
        }
        // Luego por diferencia de goles
        if (b.goalDifference !== a.goalDifference) {
            return b.goalDifference - a.goalDifference;
        }
        // Luego por goles a favor
        return b.goalsFor - a.goalsFor;
    });
    
    // Renderizar filas
    sortedStandings.forEach((team, index) => {
        const row = document.createElement('tr');
        
        // Determinar clase para las posiciones
        let positionClass = '';
        if (index < 4) {
            positionClass = 'position-libertadores';
        } else if (index < 8) {
            positionClass = 'position-sudamericana';
        } else if (index >= standings.length - 3) {
            positionClass = 'position-descenso';
        }
        
        // Generar el HTML de la fila con ajustes de estilo para mantener en línea y truncar nombres largos
        row.innerHTML = `
            <td class="position ${positionClass}">${index + 1}</td>
            <td class="team">
                <div class="team-info" style="display: flex; align-items: center; white-space: nowrap;">
                    <img 
                        src="${getTeamLogo(team.team)}" 
                        alt="${team.team}" 
                        class="team-logo" 
                        style="margin-right: 8px;"
                    >
                    <span style="
                        display: inline-block;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        max-width: 150px;
                        white-space: nowrap;
                    ">${team.team}</span>
                </div>
            </td>
            <td>${team.played || 0}</td>
            <td>${team.won || 0}</td>
            <td>${team.drawn || 0}</td>
            <td>${team.lost || 0}</td>
            <td>${team.goalsFor || 0}</td>
            <td>${team.goalsAgainst || 0}</td>
            <td>${team.goalDifference || 0}</td>
            <td class="points">${team.points || 0}</td>
        `;
        
        standingsTableBody.appendChild(row);
    });
    
    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Tabla de posiciones actualizada con ${standings.length} equipos`);
    
    // Renderizar gráfico de goles por equipo
    renderGoalsChart(standings);
    
    // Renderizar gráfico de tarjetas por equipo
    renderCardsChart(standings);
}

/**
 * Renderiza los datos de goleadores
 * @param {Array} goalscorers - Datos de goleadores
 */
function renderGoalscorers(goalscorers) {
    const scorersList = document.getElementById('scorers-list');
    
    if (!scorersList || !goalscorers || goalscorers.length === 0) {
        console.warn(`[${new Date().toLocaleTimeString('es-MX')}] No hay datos de goleadores disponibles`);
        return;
    }
    
    // Mostrar contenedor y ocultar indicador de carga
    scorersList.style.display = 'block';
    const loadingIndicator = document.getElementById('scorers-loading');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
    
    // Limpiar lista
    scorersList.innerHTML = '';
    
    // Ordenar por goles (descendente)
    const sortedScorers = [...goalscorers].sort((a, b) => b.goals - a.goals);
    
    // Tomar los 10 primeros
    const top10 = sortedScorers.slice(0, 10);
    
    // Renderizar elementos
    top10.forEach((scorer, index) => {
        const item = document.createElement('li');
        
        // Crear elementos
        const position = document.createElement('span');
        position.className = 'position';
        position.textContent = `${index + 1}.`;
        
        const playerName = document.createElement('span');
        playerName.className = 'player-name';
        playerName.textContent = scorer.name;
        
        const teamName = document.createElement('span');
        teamName.className = 'team-name';
        teamName.textContent = scorer.team;
        
        const goals = document.createElement('span');
        goals.className = 'goals';
        goals.textContent = `${scorer.goals} ${scorer.goals === 1 ? 'gol' : 'goles'}`;
        
        // Añadir elementos
        item.appendChild(position);
        item.appendChild(playerName);
        item.appendChild(teamName);
        item.appendChild(goals);
        
        // Añadir a la lista
        scorersList.appendChild(item);
    });
    
    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Tabla de goleadores actualizada con ${top10.length} jugadores`);
}

/**
 * Renderiza los datos de tarjetas
 * @param {Object} cardsData - Datos de tarjetas (estructura: {yellow: [], red: []})
 */
function renderCards(cardsData) {
    const yellowCardsList = document.getElementById('yellow-cards-list');
    const redCardsList = document.getElementById('red-cards-list');
    const cardsContainer = document.getElementById('cards-container');
    
    if (!yellowCardsList || !redCardsList || !cardsData) {
        console.warn(`[${new Date().toLocaleTimeString('es-MX')}] No hay datos de tarjetas disponibles`);
        return;
    }
    
    // Mostrar contenedor y ocultar indicador de carga
    if (cardsContainer) {
        cardsContainer.style.display = 'block';
    }
    
    const loadingIndicator = document.getElementById('cards-loading');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
    
    // Limpiar listas
    yellowCardsList.innerHTML = '';
    redCardsList.innerHTML = '';
    
    // Renderizar tarjetas amarillas
    if (cardsData.yellow && cardsData.yellow.length > 0) {
        // Ordenar por cantidad (descendente)
        const sortedYellowCards = [...cardsData.yellow].sort((a, b) => b.count - a.count);
        
        // Tomar los 5 primeros
        const top5Yellow = sortedYellowCards.slice(0, 5);
        
        // Renderizar elementos
        top5Yellow.forEach((card, index) => {
            const item = document.createElement('li');
            
            // Crear elementos
            const teamName = document.createElement('span');
            teamName.className = 'team-name';
            teamName.textContent = card.team;
            
            const count = document.createElement('span');
            count.className = 'count yellow-card-count';
            count.textContent = card.count;
            
            // Añadir elementos
            item.appendChild(teamName);
            item.appendChild(count);
            
            // Añadir a la lista
            yellowCardsList.appendChild(item);
        });
    }
    
    // Renderizar tarjetas rojas
    if (cardsData.red && cardsData.red.length > 0) {
        // Ordenar por cantidad (descendente)
        const sortedRedCards = [...cardsData.red].sort((a, b) => b.count - a.count);
        
        // Tomar los 5 primeros
        const top5Red = sortedRedCards.slice(0, 5);
        
        // Renderizar elementos
        top5Red.forEach((card, index) => {
            const item = document.createElement('li');
            
            // Crear elementos
            const teamName = document.createElement('span');
            teamName.className = 'team-name';
            teamName.textContent = card.team;
            
            const count = document.createElement('span');
            count.className = 'count red-card-count';
            count.textContent = card.count;
            
            // Añadir elementos
            item.appendChild(teamName);
            item.appendChild(count);
            
            // Añadir a la lista
            redCardsList.appendChild(item);
        });
    }
    
    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Datos de tarjetas actualizados`);
}

/**
 * Renderiza las estadísticas de equipos
 * @param {Array} teamStats - Datos de estadísticas de equipos
 */
function renderTeamStats(teamStats) {
    // Por defecto, mostrar posesión de balón
    updateTeamStatsChart('possession', teamStats);
    
    console.log(`[Métricas] Datos de estadísticas de equipos actualizados para ${teamStats.length} equipos`);
}

/**
 * Actualiza el gráfico de estadísticas de equipo según la estadística seleccionada
 * @param {string} statType - Tipo de estadística (possession, shots, passes)
 * @param {Array} teamStatsData - Datos de estadísticas de equipos
 */
function updateTeamStatsChart(statType = 'possession', teamStatsData = null) {
    // Si no se proporcionan datos, usar los almacenados
    const teamStats = teamStatsData || getStoredTeamStats();
    
    if (!teamStats || teamStats.length === 0) {
        console.warn('[Métricas] No hay datos de estadísticas de equipos disponibles');
        return;
    }
    
    const teamStatsContainer = document.getElementById('team-stats-chart');
    if (!teamStatsContainer) return;
    
    // Configurar etiquetas y datos según el tipo de estadística
    let label = 'Posesión de balón (%)';
    let dataProperty = 'possession';
    let color = 'rgba(23, 162, 184, 0.8)';
    let borderColor = 'rgba(23, 162, 184, 1)';
    
    if (statType === 'shots') {
        label = 'Tiros a puerta';
        dataProperty = 'shots';
        color = 'rgba(40, 167, 69, 0.8)';
        borderColor = 'rgba(40, 167, 69, 1)';
    } else if (statType === 'passes') {
        label = 'Pases completados';
        dataProperty = 'passes';
        color = 'rgba(0, 123, 255, 0.8)';
        borderColor = 'rgba(0, 123, 255, 1)';
    }
    
    // Ordenar equipos por la estadística seleccionada
    const sortedStats = [...teamStats].sort((a, b) => b[dataProperty] - a[dataProperty]);
    
    // Tomar los 10 primeros
    const top10 = sortedStats.slice(0, 10);
    
    // Preparar datos para el gráfico
    const teams = top10.map(stat => stat.team);
    const values = top10.map(stat => stat[dataProperty]);
    
    // Destruir gráfico anterior si existe
    if (teamStatsChart) {
        teamStatsChart.destroy();
    }
    
    // Crear gráfico
    const ctx = teamStatsContainer.getContext('2d');
    teamStatsChart = new Chart(ctx, {
        type: 'horizontalBar',
        data: {
            labels: teams,
            datasets: [{
                label: label,
                data: values,
                backgroundColor: color,
                borderColor: borderColor,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${label}: ${context.raw}${statType === 'possession' ? '%' : ''}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: label
                    },
                    ticks: {
                        precision: statType === 'possession' ? 1 : 0
                    }
                }
            }
        }
    });
}

/**
 * Obtiene los datos de estadísticas de equipos almacenados
 * @returns {Array} Datos de estadísticas de equipos
 */
function getStoredTeamStats() {
    // Si no hay datos almacenados, devolver un array vacío
    return window.teamStatsData || [];
}

/**
 * Almacena los datos de estadísticas de equipos para uso posterior
 * @param {Array} teamStats - Datos de estadísticas de equipos
 */
function storeTeamStats(teamStats) {
    window.teamStatsData = teamStats;
}

/**
 * Muestra el indicador de carga
 */
function showLoadingIndicators() {
    showLoading();
}

/**
 * Oculta el indicador de carga
 */
function hideLoadingIndicators() {
    hideLoading();
}

/**
 * Renderiza los datos de faltas
 * @param {Array} fouls - Datos de faltas
 */
function renderFouls(fouls) {
    const foulsContainer = document.getElementById('fouls-chart');
    
    if (!foulsContainer || !fouls || fouls.length === 0) {
        console.warn(`[${new Date().toLocaleTimeString('es-MX')}] No hay datos de faltas disponibles`);
        return;
    }
    
    // Obtener los top 10 equipos con más faltas
    const topFouls = [...fouls].sort((a, b) => b.count - a.count).slice(0, 10);
    
    // Preparar datos para el gráfico
    const teams = topFouls.map(foul => foul.team);
    const totalFouls = topFouls.map(foul => foul.count);
    
    // Destruir gráfico anterior si existe
    if (foulsChart) {
        foulsChart.destroy();
    }
    
    // Crear gráfico
    const ctx = foulsContainer.getContext('2d');
    foulsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: teams,
            datasets: [{
                label: 'Faltas',
                data: totalFouls,
                backgroundColor: 'rgba(108, 117, 125, 0.8)',
                borderColor: 'rgba(108, 117, 125, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Faltas: ${context.raw}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Número de faltas'
                    },
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
    
    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Gráfico de faltas actualizado con ${topFouls.length} equipos`);
}

/**
 * Carga las métricas del sistema desde la API
 */
function loadSystemMetrics() {
    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Cargando métricas del sistema...`);
    
    fetchWithErrorHandling('/api/system_metrics')
        .then(response => {
            if (response.success) {
                updateSystemMetrics(response.data);
            } else {
                console.error(`[ERROR] ${new Date().toLocaleTimeString('es-MX')}] Error al cargar métricas del sistema:`, response.error);
            }
        })
        .catch(error => {
            console.error(`[ERROR] ${new Date().toLocaleTimeString('es-MX')}] Error al cargar métricas del sistema:`, error);
        });
}

/**
 * Actualiza los elementos de la UI con las métricas del sistema
 * @param {Object} metrics - Datos de métricas del sistema
 */
function updateSystemMetrics(metrics) {
    console.log(`[${new Date().toLocaleTimeString('es-MX')}] Actualizando métricas del sistema:`, metrics);
    
    // Actualizar llamadas API
    const apiCallsElement = document.getElementById('api-calls');
    if (apiCallsElement) {
        apiCallsElement.textContent = metrics.api_calls || 0;
    }
    
    // Actualizar tasa de éxito
    const successRateElement = document.getElementById('success-rate');
    if (successRateElement) {
        successRateElement.textContent = `${metrics.success_rate || 0}%`;
    }
    
    // Actualizar tiempo de respuesta
    const responseTimeElement = document.getElementById('response-time');
    if (responseTimeElement) {
        responseTimeElement.textContent = `${metrics.avg_response_time || 0}ms`;
    }
    
    // Actualizar tiempo de actividad
    const uptimeElement = document.getElementById('uptime');
    if (uptimeElement) {
        uptimeElement.textContent = formatUptime(metrics.uptime || 0);
    }
    
    // Actualizar errores
    const errorsElement = document.getElementById('api-errors');
    if (errorsElement) {
        errorsElement.textContent = metrics.errors || 0;
    }
}

/**
 * Formatea el tiempo de actividad en segundos a formato legible
 * @param {number} seconds - Tiempo en segundos
 * @returns {string} Tiempo formateado
 */
function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
        return `${days}d ${hours}h`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

/**
 * Configura los botones de filtrado para las estadísticas
 */
function setupFilterButtons() {
    // Filtradores de temporada
    const seasonFilters = document.querySelectorAll('.season-filter');
    seasonFilters.forEach(button => {
        button.addEventListener('click', function() {
            // Remover clase activa de todos los botones
            seasonFilters.forEach(btn => btn.classList.remove('active'));
            
            // Agregar clase activa al botón clickeado
            this.classList.add('active');
            
            // Actualizar temporada seleccionada
            const selectedSeason = this.dataset.season;
            
            // Actualizar estadísticas con la temporada seleccionada
            refreshAllStats(selectedSeason);
        });
    });
    
    // Filtradores de estadísticas de equipo
    const teamStatFilters = document.querySelectorAll('.team-stat-filter');
    teamStatFilters.forEach(button => {
        button.addEventListener('click', function() {
            // Remover clase activa de todos los botones
            teamStatFilters.forEach(btn => btn.classList.remove('active'));
            
            // Agregar clase activa al botón clickeado
            this.classList.add('active');
            
            // Actualizar estadística seleccionada
            const selectedStat = this.dataset.stat;
            
            // Actualizar gráfico con la estadística seleccionada
            updateTeamStatsChart(selectedStat);
        });
    });
}

/**
 * Renderiza el gráfico de goles por equipo
 * @param {Array} standings - Datos de la tabla de posiciones
 */
function renderGoalsChart(standings) {
    const ctx = document.getElementById('goals-chart').getContext('2d');
    
    // Preparar datos de goles (simulación similar a las tarjetas)
    const teamsGoals = standings.map(team => ({
        team: team.team,
        goalsScored: team.goalsFor || Math.floor(Math.random() * 30),  // Goles anotados: simulados si no hay dato
        goalsReceived: team.goalsAgainst || Math.floor(Math.random() * 20)  // Goles recibidos: simulados si no hay dato
    }));
    
    // Ordenar equipos por total de goles (anotados + recibidos) de mayor a menor
    const sortedTeams = teamsGoals.sort((a, b) =>
        (b.goalsScored + b.goalsReceived) - (a.goalsScored + a.goalsReceived)
    );
    
    // Tomar los 10 primeros equipos
    const topTeams = sortedTeams.slice(0, 10);
    
    const teamNames = topTeams.map(team => team.team);
    const goalsScoredData = topTeams.map(team => team.goalsScored);
    const goalsReceivedData = topTeams.map(team => team.goalsReceived);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: teamNames,
            datasets: [
                {
                    label: 'Goles Anotados',
                    data: goalsScoredData,
                    backgroundColor: 'rgba(142, 68, 173, 0.6)', // Púrpura similar
                    borderColor: 'rgba(155, 89, 182, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Goles Recibidos',
                    data: goalsReceivedData,
                    backgroundColor: 'rgba(41, 128, 185, 0.6)', // Azul similar
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Número de Goles'
                    },
                    stacked: true
                },
                x: {
                    stacked: true
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Equipos por Goles'
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });
}


/**
 * Renderiza el gráfico de tarjetas por equipo
 * @param {Array} standings - Datos de la tabla de posiciones
 */
function renderCardsChart(standings) {
    const ctx = document.getElementById('cards-chart').getContext('2d');
    
    // Calcular tarjetas amarillas y rojas por equipo (datos simulados)
    const teamsCards = standings.map(team => ({
        team: team.team,
        yellowCards: Math.floor(Math.random() * 20) + 5, // Entre 5 y 25
        redCards: Math.floor(Math.random() * 5) // Entre 0 y 4
    }));
    
    // Ordenar equipos por total de tarjetas de mayor a menor
    const sortedTeams = teamsCards.sort((a, b) => 
        (b.yellowCards + b.redCards) - (a.yellowCards + a.redCards)
    );
    
    // Tomar los 10 primeros equipos
    const topTeams = sortedTeams.slice(0, 10);
    
    const teamNames = topTeams.map(team => team.team);
    const yellowCardsData = topTeams.map(team => team.yellowCards);
    const redCardsData = topTeams.map(team => team.redCards);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: teamNames,
            datasets: [
                {
                    label: 'Tarjetas Amarillas',
                    data: yellowCardsData,
                    backgroundColor: 'rgba(255, 206, 86, 0.6)', // Color amarillo
                    borderColor: 'rgba(255, 206, 86, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Tarjetas Rojas',
                    data: redCardsData,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)', // Color rojo
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Número de Tarjetas'
                    },
                    stacked: true
                },
                x: {
                    stacked: true
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Equipos por Tarjetas'
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });
}
