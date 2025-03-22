"""
Liga MX Bot - Aplicación Web
Incluye sistema de monitoreo, logging y visualización de datos
"""
import os
import sys
import json
import logging
import datetime
import traceback
from logging.handlers import RotatingFileHandler
import pytz
import yaml
import structlog
from flask import Flask, render_template, jsonify, request, Response, redirect, url_for
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY, Gauge
from functools import lru_cache
import time
import subprocess
import threading

# Agregar el directorio padre al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos del proyecto
try:
    from core.livescore_client import LiveScoreClient
    from core.config import (
        LIVESCORE_API_KEY,
        LIVESCORE_API_SECRET,
        LIGA_MX_COMPETITION_ID
    )
    config_available = True
except ImportError:
    print("No se pudo importar la configuración. Se usarán datos de ejemplo.")
    config_available = False

# Configuración de la aplicación
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Zona horaria de México (UTC-6)
MEXICO_TZ = pytz.timezone('America/Mexico_City')

# Inicialización del cliente de LiveScore
livescore_client = None
if config_available:
    try:
        livescore_client = LiveScoreClient(LIVESCORE_API_KEY, LIVESCORE_API_SECRET)
    except Exception as e:
        print(f"Error al inicializar el cliente de LiveScore: {e}")

# Configuración de logging estructurado
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configurar logging estructurado con structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configurar handler para archivos
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "liga_mx_web.log"),
    maxBytes=10485760,  # 10MB
    backupCount=10
)

# Configurar handler para consola
console_handler = logging.StreamHandler()

# Configurar formato para ambos handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Configurar logger de Flask
app.logger.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.addHandler(console_handler)

# Logger estructurado para la aplicación
logger = structlog.get_logger("liga_mx_web")

# Métricas de Prometheus
MATCHES_VIEWED = Counter(
    'liga_mx_matches_viewed_total',
    'Número total de veces que se han visto los partidos'
)

STATS_VIEWED = Counter(
    'liga_mx_stats_viewed_total',
    'Número total de veces que se han visto las estadísticas'
)

API_CALLS = Counter('api_calls_total', 'Total de llamadas a la API', ['endpoint'])
API_ERRORS = Counter('api_errors_total', 'Total de errores en llamadas a la API', ['endpoint'])
API_REQUEST_DURATION = Histogram('api_request_duration_seconds', 'Duración de las solicitudes a la API', ['endpoint'])
ERROR_COUNTER = Counter('errors_total', 'Total de errores', ['type'])

ACTIVE_USERS = Gauge(
    'liga_mx_active_users',
    'Número de usuarios activos en la aplicación'
)

# Incrementar contador de usuarios activos al iniciar la aplicación
ACTIVE_USERS.inc()

# Contadores para métricas del sistema
system_metrics = {
    'api_calls': 0,
    'api_errors': 0,
    'api_total_time': 0,
    'api_request_count': 0,
    'startup_time': time.time()
}

# Configuración de Grafana
GRAFANA_URL = os.getenv('GRAFANA_URL', 'http://localhost:3000')
GRAFANA_USER = os.getenv('GRAFANA_USER', 'admin')
GRAFANA_PASSWORD = os.getenv('GRAFANA_PASSWORD', 'admin')

# Función para iniciar los servicios de monitoreo en segundo plano
def start_monitoring_services():
    """Inicia los servicios de monitoreo (Prometheus y Grafana) en segundo plano"""
    try:
        # Comprobar si Docker está disponible
        docker_check = subprocess.run(["docker", "--version"], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     check=False)
        
        if docker_check.returncode == 0:
            logger.info("Docker disponible, iniciando servicios de monitoreo...")
            # Docker está disponible, intentamos iniciar los servicios
            subprocess.run(["docker-compose", "up", "-d"], 
                          cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            logger.info("Servicios de monitoreo iniciados correctamente")
            
            # Configurar Grafana después de unos segundos
            threading.Timer(10.0, setup_grafana).start()
        else:
            logger.warning("Docker no está disponible. Las integraciones con Grafana y Prometheus no estarán disponibles.")
            logger.warning("La aplicación funcionará pero sin la visualización de Grafana.")
    except Exception as e:
        logger.error(f"Error al iniciar servicios de monitoreo: {e}")
        logger.warning("La aplicación continuará funcionando sin los servicios de monitoreo.")

def setup_grafana():
    """Configura Grafana con datasources y dashboards"""
    try:
        from grafana_setup import setup_grafana as setup
        setup()
        logger.info("Grafana configurado correctamente")
    except Exception as e:
        logger.error(f"Error al configurar Grafana: {e}")

@app.route('/metrics')
def metrics():
    """
    Endpoint para métricas de Prometheus
    """
    return Response(generate_latest(REGISTRY), mimetype='text/plain')

@app.route('/')
def index():
    """
    Página principal
    """
    logger.info("Página principal visitada", 
                user_agent=request.headers.get('User-Agent'),
                remote_addr=request.remote_addr)
    MATCHES_VIEWED.inc()
    return render_template('index.html')

@app.route('/metricas')
def metricas():
    """
    Página de métricas y estadísticas
    """
    logger.info("Página de métricas visitada", 
                user_agent=request.headers.get('User-Agent'),
                remote_addr=request.remote_addr)
    STATS_VIEWED.inc()
    return render_template('metricas.html')

@app.route('/dashboard')
def dashboard():
    """
    Dashboard de monitoreo
    """
    logger.info("Dashboard de monitoreo visitado", 
                user_agent=request.headers.get('User-Agent'),
                remote_addr=request.remote_addr)
    return render_template('dashboard.html')

@app.route('/grafana')
def grafana():
    """
    Página para visualizar dashboards de Grafana
    """
    logger.info("Página de Grafana visitada", 
                user_agent=request.headers.get('User-Agent'),
                remote_addr=request.remote_addr)
    # Verificar si Docker está disponible
    docker_check = subprocess.run(["docker", "--version"], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                check=False)
    
    if docker_check.returncode == 0:
        return render_template('grafana.html')
    else:
        # Si Docker no está disponible, mostrar página de métricas alternativa
        logger.warning("Docker no disponible, redirigiendo a página de métricas alternativa")
        return redirect(url_for('metricas'))

@app.route('/grafana-redirect')
def grafana_redirect():
    """
    Redirección a la interfaz de Grafana
    """
    logger.info("Redirección a Grafana", 
                user_agent=request.headers.get('User-Agent'),
                remote_addr=request.remote_addr)
    return redirect(GRAFANA_URL)

@app.route('/api/grafana-info')
def api_grafana_info():
    """
    API para obtener información de Grafana
    """
    API_CALLS.labels(endpoint='/api/grafana-info').inc()
    return jsonify({
        'url': GRAFANA_URL,
        'dashboards': [
            {
                'title': 'Liga MX - Estadísticas',
                'url': f"{GRAFANA_URL}/d/liga-mx-estadisticas/liga-mx-estadisticas",
                'description': 'Estadísticas de la Liga MX en tiempo real'
            },
            {
                'title': 'Liga MX - Sistema',
                'url': f"{GRAFANA_URL}/d/liga-mx-sistema/liga-mx-sistema",
                'description': 'Monitoreo del sistema del bot de Liga MX'
            }
        ]
    })

@app.route('/api/matches')
def api_matches():
    """
    API para obtener partidos de la Liga MX
    """
    API_CALLS.labels(endpoint='/api/matches').inc()
    system_metrics['api_calls'] += 1
    start_time = datetime.datetime.now()
    try:
        # Intentar cargar los partidos desde el cliente de LiveScore
        if livescore_client:
            matches = livescore_client.get_liga_mx_matches(live_only=False)
            
            # Si no hay partidos, usar datos de ejemplo
            if not matches:
                matches = get_sample_matches()
                
            # Asegurarse de que todas las horas estén en UTC-6 (hora de México)
            for match in matches:
                if 'time' in match and match['time']:
                    # Parsear la hora
                    time_parts = match['time'].split(':')
                    if len(time_parts) >= 2:
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        
                        # Convertir de UTC a UTC-6 (hora de México)
                        # Si la hora viene en UTC, restar 6 horas
                        hour = (hour - 6) % 24
                        
                        # Formatear la hora de nuevo
                        match['time'] = f"{hour:02d}:{minute:02d}"
                        
                        # Log para depuración
                        logger.debug(f"Hora convertida a UTC-6: {match['time']}")
            
            # Formatear los partidos para la respuesta
            formatted_matches = []
            for match in matches:
                formatted_match = {
                    "id": match.get('id', ''),
                    "date": match.get('date', ''),
                    "time": match.get('time', ''),
                    "status": match.get('status', ''),
                    "competition": "Liga MX - Jornada " + str(match.get('round', '13')),
                    "homeTeam": {
                        "name": match.get('home_name', ''),
                        "logo": get_team_logo(match.get('home_name', '')),
                        "score": match.get('score', '').split(' - ')[0] if ' - ' in match.get('score', '') else ''
                    },
                    "awayTeam": {
                        "name": match.get('away_name', ''),
                        "logo": get_team_logo(match.get('away_name', '')),
                        "score": match.get('score', '').split(' - ')[1] if ' - ' in match.get('score', '') else ''
                    },
                    "venue": match.get('location', '')
                }
                formatted_matches.append(formatted_match)
            
            logger.info("Partidos obtenidos correctamente", 
                        count=len(formatted_matches),
                        source="livescore_api")
            
            response = {
                'success': True,
                'matches': formatted_matches if formatted_matches else get_sample_matches()
            }
        else:
            # Si no hay cliente, usar datos de ejemplo
            logger.warning("Cliente LiveScore no disponible, usando datos de ejemplo")
            response = {
                'success': True,
                'matches': get_sample_matches()
            }
    except Exception as e:
        error_msg = str(e)
        logger.error("Error al obtener partidos", 
                    error=error_msg,
                    traceback=traceback.format_exc())
        ERROR_COUNTER.labels(type='api_matches').inc()
        API_ERRORS.labels(endpoint='/api/matches').inc()
        system_metrics['api_errors'] += 1
        response = {
            'success': False,
            'error': error_msg,
            'matches': get_sample_matches()
        }
    
    # Registrar duración de la solicitud
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    API_REQUEST_DURATION.labels(endpoint='/api/matches').observe(duration)
    system_metrics['api_total_time'] += duration
    system_metrics['api_request_count'] += 1
    
    return jsonify(response)

@app.route('/api/stats')
def api_stats():
    """
    API para obtener estadísticas de la Liga MX
    """
    API_CALLS.labels(endpoint='/api/stats').inc()
    system_metrics['api_calls'] += 1
    start_time = datetime.datetime.now()
    STATS_VIEWED.inc()
    season = request.args.get('season', 'Clausura 2025')
    
    try:
        # Usar estadísticas cacheadas para mejorar la velocidad
        stats = get_cached_stats(season)
        
        # Registrar éxito en la solicitud
        logger.info("Estadísticas obtenidas correctamente", 
                    season=season)
        
        response = {
            'success': True,
            'data': stats
        }
    except Exception as e:
        error_msg = str(e)
        logger.error("Error al obtener estadísticas", 
                    error=error_msg,
                    season=season,
                    traceback=traceback.format_exc())
        
        # Incrementar contador de errores
        ERROR_COUNTER.labels(type='api_stats').inc()
        API_ERRORS.labels(endpoint='/api/stats').inc()
        system_metrics['api_errors'] += 1
        
        response = {
            'success': False,
            'error': error_msg,
            'message': "Error al obtener estadísticas"
        }
    
    # Registrar duración de la solicitud
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    API_REQUEST_DURATION.labels(endpoint='/api/stats').observe(duration)
    system_metrics['api_total_time'] += duration
    system_metrics['api_request_count'] += 1
    
    return jsonify(response)

@app.route('/api/logs')
def api_logs():
    """
    API para obtener logs de la aplicación (solo para administradores)
    """
    API_CALLS.labels(endpoint='/api/logs').inc()
    try:
        # Leer los últimos 100 logs
        logs = []
        log_file = os.path.join(LOG_DIR, "liga_mx_web.log")
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-100:]:
                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        logs.append({"message": line.strip()})
        
        return jsonify({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        logger.error("Error al obtener logs", 
                    error=str(e),
                    traceback=traceback.format_exc())
        ERROR_COUNTER.labels(type='api_logs').inc()
        API_ERRORS.labels(endpoint='/api/logs').inc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/metrics_data')
def api_metrics_data():
    """
    API para obtener datos de métricas para el dashboard
    """
    API_CALLS.labels(endpoint='/api/metrics_data').inc()
    try:
        # Generar datos de métricas de ejemplo
        metrics_data = {
            'matches_viewed': MATCHES_VIEWED._value.get(),
            'stats_viewed': STATS_VIEWED._value.get(),
            'active_users': ACTIVE_USERS._value,
            'errors': {
                'api_matches': ERROR_COUNTER.labels(type='api_matches')._value.get(),
                'api_stats': ERROR_COUNTER.labels(type='api_stats')._value.get(),
                'api_logs': ERROR_COUNTER.labels(type='api_logs')._value.get()
            },
            'request_durations': {
                'api_matches': API_REQUEST_DURATION.labels(endpoint='/api/matches')._sum.get(),
                'api_stats': API_REQUEST_DURATION.labels(endpoint='/api/stats')._sum.get()
            }
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics_data
        })
    except Exception as e:
        logger.error("Error al obtener datos de métricas", 
                    error=str(e),
                    traceback=traceback.format_exc())
        ERROR_COUNTER.labels(type='api_metrics_data').inc()
        API_ERRORS.labels(endpoint='/api/metrics_data').inc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/about')
def api_about():
    """
    API para obtener información sobre el bot
    """
    API_CALLS.labels(endpoint='/api/about').inc()
    return jsonify({
        'success': True,
        'name': 'Liga MX Bot',
        'version': '2.0.0',
        'description': 'Bot para seguir la Liga MX',
        'author': 'Equipo de Desarrollo',
        'repository': 'https://github.com/example/liga-mx-bot'
    })

@app.route('/api/system_metrics')
def api_system_metrics():
    """
    API para obtener métricas del sistema
    """
    API_CALLS.labels(endpoint='/api/system_metrics').inc()
    system_metrics['api_calls'] += 1
    
    try:
        # Calcular tasa de éxito
        success_rate = 100.0
        if system_metrics['api_calls'] > 0:
            success_rate = ((system_metrics['api_calls'] - system_metrics['api_errors']) / system_metrics['api_calls']) * 100.0
        
        # Calcular tiempo de respuesta promedio (ms)
        avg_response_time = 0
        if system_metrics['api_request_count'] > 0:
            avg_response_time = (system_metrics['api_total_time'] / system_metrics['api_request_count']) * 1000  # Convertir a ms
        
        response = {
            'success': True,
            'data': {
                'api_calls': system_metrics['api_calls'],
                'success_rate': round(success_rate, 1),
                'avg_response_time': round(avg_response_time, 0),
                'uptime': get_uptime_seconds(),
                'errors': system_metrics['api_errors']
            }
        }
        return jsonify(response)
    
    except Exception as e:
        logger.error("Error al obtener métricas del sistema", 
                    error=str(e),
                    traceback=traceback.format_exc())
        
        API_ERRORS.labels(endpoint='/api/system_metrics').inc()
        system_metrics['api_errors'] += 1
        return jsonify({
            'success': False,
            'error': str(e),
            'message': "Error al obtener métricas del sistema"
        })

# Implementar cache para las estadísticas
@lru_cache(maxsize=4)  # Caché para las últimas 4 temporadas consultadas
def get_cached_stats(season):
    """
    Obtiene estadísticas con caché para mejorar la velocidad
    """
    # Si se cambia a datos reales, añadir lógica para invalidar caché
    # cuando los datos se actualicen
    return get_sample_stats()

def get_team_logo(team_name):
    """
    Obtiene el logo de un equipo
    """
    # Normalizar el nombre del equipo
    team_name = team_name.lower().strip()
    
    # Mapeo de nombres de equipos a logos
    team_logos = {
        'america': '/static/img/ligamx/america.png',
        'atlas': '/static/img/ligamx/atlas.png',
        'atlético san luis': '/static/img/ligamx/sanluis.png',
        'atletico san luis': '/static/img/ligamx/sanluis.png',
        'cruz azul': '/static/img/ligamx/cruzazul.png',
        'guadalajara': '/static/img/ligamx/guadalajara.png',
        'chivas': '/static/img/ligamx/guadalajara.png',
        'juárez': '/static/img/ligamx/juarez.png',
        'juarez': '/static/img/ligamx/juarez.png',
        'león': '/static/img/ligamx/leon.png',
        'leon': '/static/img/ligamx/leon.png',
        'mazatlán': '/static/img/ligamx/mazatlan.png',
        'mazatlan': '/static/img/ligamx/mazatlan.png',
        'monterrey': '/static/img/ligamx/monterrey.png',
        'necaxa': '/static/img/ligamx/necaxa.png',
        'pachuca': '/static/img/ligamx/pachuca.png',
        'puebla': '/static/img/ligamx/puebla.png',
        'pumas unam': '/static/img/ligamx/pumas.png',
        'querétaro': '/static/img/ligamx/queretaro.png',
        'queretaro': '/static/img/ligamx/queretaro.png',
        'santos laguna': '/static/img/ligamx/santos.png',
        'tigres uanl': '/static/img/ligamx/tigres.png',
        'tijuana': '/static/img/ligamx/tijuana.png',
        'toluca': '/static/img/ligamx/toluca.png'
    }
    
    # Buscar el logo del equipo
    for key, logo in team_logos.items():
        if key in team_name or team_name in key:
            return logo
    
    # Si no se encuentra, devolver un logo por defecto
    return '/static/img/ligamx/default.png'

def get_sample_matches():
    """
    Devuelve partidos de ejemplo para cuando no hay configuración disponible
    """
    return [
        {
            "id": "1",
            "date": "2025-03-28",
            "time": "19:00",
            "status": "Not Started",
            "competition": "Liga MX - Jornada 13",
            "homeTeam": {
                "name": "Necaxa",
                "logo": "/static/img/ligamx/necaxa.png",
                "score": ""
            },
            "awayTeam": {
                "name": "Querétaro",
                "logo": "/static/img/ligamx/queretaro.png",
                "score": ""
            },
            "venue": "Estadio Victoria"
        },
        {
            "id": "2",
            "date": "2025-03-28",
            "time": "21:00",
            "status": "Not Started",
            "competition": "Liga MX - Jornada 13",
            "homeTeam": {
                "name": "Mazatlán",
                "logo": "/static/img/ligamx/mazatlan.png",
                "score": ""
            },
            "awayTeam": {
                "name": "Atlas",
                "logo": "/static/img/ligamx/atlas.png",
                "score": ""
            },
            "venue": "Estadio de Mazatlán"
        },
        {
            "id": "3",
            "date": "2025-03-29",
            "time": "17:00",
            "status": "Not Started",
            "competition": "Liga MX - Jornada 13",
            "homeTeam": {
                "name": "Juárez",
                "logo": "/static/img/ligamx/juarez.png",
                "score": ""
            },
            "awayTeam": {
                "name": "Puebla",
                "logo": "/static/img/ligamx/puebla.png",
                "score": ""
            },
            "venue": "Estadio Olímpico Benito Juárez"
        },
        {
            "id": "4",
            "date": "2025-03-29",
            "time": "17:00",
            "status": "Not Started",
            "competition": "Liga MX - Jornada 13",
            "homeTeam": {
                "name": "Toluca",
                "logo": "/static/img/ligamx/toluca.png",
                "score": ""
            },
            "awayTeam": {
                "name": "Pachuca",
                "logo": "/static/img/ligamx/pachuca.png",
                "score": ""
            },
            "venue": "Estadio Nemesio Díez"
        },
        {
            "id": "5",
            "date": "2025-03-29",
            "time": "19:05",
            "status": "Not Started",
            "competition": "Liga MX - Jornada 13",
            "homeTeam": {
                "name": "América",
                "logo": "/static/img/ligamx/america.png",
                "score": ""
            },
            "awayTeam": {
                "name": "Tigres UANL",
                "logo": "/static/img/ligamx/tigres.png",
                "score": ""
            },
            "venue": "Estadio Azteca"
        },
        {
            "id": "6",
            "date": "2025-03-29",
            "time": "21:05",
            "status": "Not Started",
            "competition": "Liga MX - Jornada 13",
            "homeTeam": {
                "name": "Guadalajara",
                "logo": "/static/img/ligamx/guadalajara.png",
                "score": ""
            },
            "awayTeam": {
                "name": "Cruz Azul",
                "logo": "/static/img/ligamx/cruzazul.png",
                "score": ""
            },
            "venue": "Estadio Akron"
        },
        {
            "id": "7",
            "date": "2025-03-29",
            "time": "21:10",
            "status": "Not Started",
            "competition": "Liga MX - Jornada 13",
            "homeTeam": {
                "name": "Monterrey",
                "logo": "/static/img/ligamx/monterrey.png",
                "score": ""
            },
            "awayTeam": {
                "name": "Tijuana",
                "logo": "/static/img/ligamx/tijuana.png",
                "score": ""
            },
            "venue": "Estadio BBVA"
        },
        {
            "id": "8",
            "date": "2025-03-30",
            "time": "17:00",
            "status": "Not Started",
            "competition": "Liga MX - Jornada 13",
            "homeTeam": {
                "name": "Santos Laguna",
                "logo": "/static/img/ligamx/santos.png",
                "score": ""
            },
            "awayTeam": {
                "name": "Atlético San Luis",
                "logo": "/static/img/ligamx/sanluis.png",
                "score": ""
            },
            "venue": "Estadio Corona"
        },
        {
            "id": "9",
            "date": "2025-03-30",
            "time": "19:00",
            "status": "Not Started",
            "competition": "Liga MX - Jornada 13",
            "homeTeam": {
                "name": "León",
                "logo": "/static/img/ligamx/leon.png",
                "score": ""
            },
            "awayTeam": {
                "name": "Pumas UNAM",
                "logo": "/static/img/ligamx/pumas.png",
                "score": ""
            },
            "venue": "Estadio León"
        }
    ]

def get_sample_stats():
    """
    Devuelve estadísticas de ejemplo
    """
    return {
        "standings": [
            {"position": 1, "team": "América", "points": 30, "played": 12, "won": 9, "drawn": 3, "lost": 0, "gf": 25, "ga": 8, "gd": 17},
            {"position": 2, "team": "Cruz Azul", "points": 27, "played": 12, "won": 8, "drawn": 3, "lost": 1, "gf": 20, "ga": 7, "gd": 13},
            {"position": 3, "team": "Tigres UANL", "points": 25, "played": 12, "won": 7, "drawn": 4, "lost": 1, "gf": 18, "ga": 8, "gd": 10},
            {"position": 4, "team": "Monterrey", "points": 23, "played": 12, "won": 7, "drawn": 2, "lost": 3, "gf": 19, "ga": 12, "gd": 7},
            {"position": 5, "team": "Toluca", "points": 21, "played": 12, "won": 6, "drawn": 3, "lost": 3, "gf": 22, "ga": 15, "gd": 7},
            {"position": 6, "team": "Pachuca", "points": 20, "played": 12, "won": 6, "drawn": 2, "lost": 4, "gf": 17, "ga": 14, "gd": 3},
            {"position": 7, "team": "Guadalajara", "points": 19, "played": 12, "won": 5, "drawn": 4, "lost": 3, "gf": 15, "ga": 12, "gd": 3},
            {"position": 8, "team": "León", "points": 18, "played": 12, "won": 5, "drawn": 3, "lost": 4, "gf": 14, "ga": 13, "gd": 1},
            {"position": 9, "team": "Pumas UNAM", "points": 17, "played": 12, "won": 5, "drawn": 2, "lost": 5, "gf": 16, "ga": 16, "gd": 0},
            {"position": 10, "team": "Santos Laguna", "points": 16, "played": 12, "won": 4, "drawn": 4, "lost": 4, "gf": 15, "ga": 15, "gd": 0},
            {"position": 11, "team": "Atlas", "points": 15, "played": 12, "won": 4, "drawn": 3, "lost": 5, "gf": 13, "ga": 14, "gd": -1},
            {"position": 12, "team": "Atlético San Luis", "points": 14, "played": 12, "won": 4, "drawn": 2, "lost": 6, "gf": 12, "ga": 16, "gd": -4},
            {"position": 13, "team": "Necaxa", "points": 13, "played": 12, "won": 3, "drawn": 4, "lost": 5, "gf": 11, "ga": 15, "gd": -4},
            {"position": 14, "team": "Tijuana", "points": 12, "played": 12, "won": 3, "drawn": 3, "lost": 6, "gf": 10, "ga": 15, "gd": -5},
            {"position": 15, "team": "Puebla", "points": 11, "played": 12, "won": 3, "drawn": 2, "lost": 7, "gf": 9, "ga": 17, "gd": -8},
            {"position": 16, "team": "Mazatlán", "points": 10, "played": 12, "won": 2, "drawn": 4, "lost": 6, "gf": 8, "ga": 16, "gd": -8},
            {"position": 17, "team": "Querétaro", "points": 9, "played": 12, "won": 2, "drawn": 3, "lost": 7, "gf": 7, "ga": 18, "gd": -11},
            {"position": 18, "team": "Juárez", "points": 7, "played": 12, "won": 1, "drawn": 4, "lost": 7, "gf": 6, "ga": 20, "gd": -14}
        ],
        "top_scorers": [
            {"player": "Julián Quiñones", "team": "América", "goals": 10},
            {"player": "André-Pierre Gignac", "team": "Tigres UANL", "goals": 9},
            {"player": "Germán Berterame", "team": "Monterrey", "goals": 8},
            {"player": "Uriel Antuna", "team": "Cruz Azul", "goals": 7},
            {"player": "Alexis Vega", "team": "Guadalajara", "goals": 7},
            {"player": "Paulinho", "team": "Toluca", "goals": 6},
            {"player": "Nicolás Ibáñez", "team": "Tigres UANL", "goals": 6},
            {"player": "Eduardo Aguirre", "team": "Santos Laguna", "goals": 5},
            {"player": "Rodrigo Aguirre", "team": "Necaxa", "goals": 5},
            {"player": "César Huerta", "team": "Pumas UNAM", "goals": 5}
        ],
        "cards": {
            "yellow": [
                {"team": "Juárez", "count": 45},
                {"team": "Puebla", "count": 42},
                {"team": "Tijuana", "count": 40},
                {"team": "Querétaro", "count": 38},
                {"team": "Mazatlán", "count": 37}
            ],
            "red": [
                {"team": "Juárez", "count": 5},
                {"team": "Tijuana", "count": 4},
                {"team": "Querétaro", "count": 3},
                {"team": "Puebla", "count": 3},
                {"team": "Mazatlán", "count": 3}
            ]
        },
        "fouls": [
            {"team": "Juárez", "count": 180},
            {"team": "Puebla", "count": 175},
            {"team": "Tijuana", "count": 168},
            {"team": "Querétaro", "count": 165},
            {"team": "Mazatlán", "count": 160}
        ],
        "metrics": {
            "total_goals": 235,
            "avg_goals_per_match": 2.45,
            "home_wins_percentage": 45,
            "away_wins_percentage": 30,
            "draws_percentage": 25
        },
        "system_metrics": {
            "api_calls": {
                "total": 1250,
                "success_rate": 98.5,
                "avg_response_time": 0.35
            },
            "errors": {
                "total": 25,
                "by_type": {
                    "api_matches": 12,
                    "api_stats": 8,
                    "api_logs": 5
                }
            },
            "performance": {
                "memory_usage": "125MB",
                "cpu_usage": "15%",
                "uptime": "7d 12h 45m"
            }
        }
    }

def get_uptime_seconds():
    """
    Obtiene el tiempo de actividad del servidor en segundos
    """
    return int(time.time() - system_metrics['startup_time'])

if __name__ == '__main__':
    # Registrar inicio de la aplicación
    logger.info("Aplicación iniciada", version="2.0.0")
    start_monitoring_services()
    app.run(host='127.0.0.1', port=8080, debug=True)
