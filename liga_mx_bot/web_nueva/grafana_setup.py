"""
Liga MX Bot - Configuración de Grafana
Script para configurar automáticamente Grafana con datasources y dashboards
"""
import os
import json
import time
import requests
from grafana_api.grafana_face import GrafanaFace
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Grafana
GRAFANA_URL = os.getenv('GRAFANA_URL', 'http://localhost:3000')
GRAFANA_USER = os.getenv('GRAFANA_USER', 'admin')
GRAFANA_PASSWORD = os.getenv('GRAFANA_PASSWORD', 'admin')
PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://prometheus:9090')

# Esperar a que Grafana esté listo
def wait_for_grafana():
    """Espera a que Grafana esté listo para recibir solicitudes"""
    print("Esperando a que Grafana esté disponible...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health")
            if response.status_code == 200:
                print("Grafana está listo!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"Reintentando en 2 segundos... ({i+1}/{max_retries})")
        time.sleep(2)
    
    print("No se pudo conectar a Grafana")
    return False

# Configurar Grafana
def setup_grafana():
    """Configura Grafana con datasources y dashboards"""
    if not wait_for_grafana():
        return False
    
    # Conectar a Grafana API
    grafana = GrafanaFace(
        auth=(GRAFANA_USER, GRAFANA_PASSWORD),
        host=GRAFANA_URL
    )
    
    # Crear datasource de Prometheus
    try:
        datasources = grafana.datasource.list_datasources()
        prometheus_exists = any(ds['name'] == 'Prometheus' for ds in datasources)
        
        if not prometheus_exists:
            print("Creando datasource de Prometheus...")
            grafana.datasource.create_datasource({
                'name': 'Prometheus',
                'type': 'prometheus',
                'url': PROMETHEUS_URL,
                'access': 'proxy',
                'isDefault': True
            })
            print("Datasource de Prometheus creado exitosamente")
        else:
            print("Datasource de Prometheus ya existe")
            
        # Crear dashboards
        create_dashboards(grafana)
        
        return True
    except Exception as e:
        print(f"Error al configurar Grafana: {e}")
        return False

# Crear dashboards
def create_dashboards(grafana):
    """Crea dashboards para Liga MX en Grafana"""
    print("Creando dashboards de Liga MX...")
    
    # Dashboard de Liga MX
    liga_mx_dashboard = {
        "dashboard": {
            "id": None,
            "title": "Liga MX - Estadísticas",
            "tags": ["liga-mx", "futbol", "mexico"],
            "timezone": "browser",
            "schemaVersion": 16,
            "version": 1,
            "refresh": "30s",
            "panels": [
                # Panel de estadísticas de API
                {
                    "id": 1,
                    "title": "Llamadas a la API",
                    "type": "stat",
                    "datasource": "Prometheus",
                    "targets": [
                        {
                            "expr": "api_calls_total",
                            "legendFormat": "Llamadas Totales",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {
                        "h": 8,
                        "w": 8,
                        "x": 0,
                        "y": 0
                    }
                },
                # Panel de errores de API
                {
                    "id": 2,
                    "title": "Errores de API",
                    "type": "stat",
                    "datasource": "Prometheus",
                    "targets": [
                        {
                            "expr": "api_errors_total",
                            "legendFormat": "Errores Totales",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {
                        "h": 8,
                        "w": 8,
                        "x": 8,
                        "y": 0
                    }
                },
                # Panel de usuarios activos
                {
                    "id": 3,
                    "title": "Usuarios Activos",
                    "type": "gauge",
                    "datasource": "Prometheus",
                    "targets": [
                        {
                            "expr": "liga_mx_active_users",
                            "legendFormat": "Usuarios Activos",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {
                        "h": 8,
                        "w": 8,
                        "x": 16,
                        "y": 0
                    },
                    "options": {
                        "fieldOptions": {
                            "calcs": ["last"],
                            "defaults": {
                                "max": 100,
                                "min": 0
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    { "color": "green", "value": None },
                                    { "color": "orange", "value": 50 },
                                    { "color": "red", "value": 80 }
                                ]
                            }
                        }
                    }
                },
                # Gráfico de duración de solicitudes a la API
                {
                    "id": 4,
                    "title": "Duración de Solicitudes a la API",
                    "type": "graph",
                    "datasource": "Prometheus",
                    "targets": [
                        {
                            "expr": "rate(api_request_duration_seconds_sum[5m]) / rate(api_request_duration_seconds_count[5m])",
                            "legendFormat": "{{endpoint}}",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {
                        "h": 8,
                        "w": 24,
                        "x": 0,
                        "y": 8
                    }
                },
                # Gráfico de vistas de partidos y estadísticas
                {
                    "id": 5,
                    "title": "Vistas de Partidos y Estadísticas",
                    "type": "graph",
                    "datasource": "Prometheus",
                    "targets": [
                        {
                            "expr": "liga_mx_matches_viewed_total",
                            "legendFormat": "Partidos Vistos",
                            "refId": "A"
                        },
                        {
                            "expr": "liga_mx_stats_viewed_total",
                            "legendFormat": "Estadísticas Vistas",
                            "refId": "B"
                        }
                    ],
                    "gridPos": {
                        "h": 8,
                        "w": 24,
                        "x": 0,
                        "y": 16
                    }
                }
            ]
        },
        "folderId": 0,
        "overwrite": True
    }
    
    # Dashboard de sistema
    system_dashboard = {
        "dashboard": {
            "id": None,
            "title": "Liga MX - Sistema",
            "tags": ["liga-mx", "sistema", "monitoreo"],
            "timezone": "browser",
            "schemaVersion": 16,
            "version": 1,
            "refresh": "10s",
            "panels": [
                # Panel de errores por tipo
                {
                    "id": 1,
                    "title": "Errores por Tipo",
                    "type": "piechart",
                    "datasource": "Prometheus",
                    "targets": [
                        {
                            "expr": "errors_total",
                            "legendFormat": "{{type}}",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {
                        "h": 9,
                        "w": 12,
                        "x": 0,
                        "y": 0
                    }
                },
                # Panel de tiempo de actividad
                {
                    "id": 2,
                    "title": "Tiempo de Actividad (minutos)",
                    "type": "stat",
                    "datasource": "Prometheus",
                    "targets": [
                        {
                            "expr": "time() - process_start_time_seconds",
                            "legendFormat": "Tiempo de Actividad",
                            "refId": "A"
                        }
                    ],
                    "options": {
                        "colorMode": "value",
                        "graphMode": "area",
                        "justifyMode": "auto",
                        "orientation": "auto",
                        "reduceOptions": {
                            "calcs": ["lastNotNull"],
                            "fields": "",
                            "values": False
                        }
                    },
                    "gridPos": {
                        "h": 9,
                        "w": 12,
                        "x": 12,
                        "y": 0
                    }
                }
            ]
        },
        "folderId": 0,
        "overwrite": True
    }
    
    try:
        # Importar dashboards
        grafana.dashboard.update_dashboard(liga_mx_dashboard)
        print("Dashboard de Liga MX creado exitosamente")
        
        grafana.dashboard.update_dashboard(system_dashboard)
        print("Dashboard de Sistema creado exitosamente")
    except Exception as e:
        print(f"Error al crear dashboards: {e}")

if __name__ == "__main__":
    setup_grafana()
