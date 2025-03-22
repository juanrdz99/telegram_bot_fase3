# Bot de Telegram para Liga MX

Bot de Telegram para notificaciones en tiempo real de partidos de la Liga MX usando la API de Live Score.

## Características

- Notificaciones en tiempo real de partidos de Liga MX
- Actualizaciones de goles, tarjetas, sustituciones y estadísticas
- Notificaciones de inicio, medio tiempo y final de partido
- Opciones para notificar partidos de toda la semana, solo fin de semana o jornada actual

## Estructura del Proyecto

```
liga_mx_bot/
├── core/                   # Módulos principales del bot
│   ├── config.py           # Configuración y credenciales
│   ├── formatter.py        # Formateador de mensajes
│   ├── livescore_client.py # Cliente para la API de LiveScore
│   ├── match_tracker.py    # Rastreador de partidos
│   ├── enhanced_match_tracker.py # Rastreador mejorado
│   ├── telegram_client.py  # Cliente para la API de Telegram
│   └── main.py             # Aplicación principal
├── scripts/                # Scripts ejecutables
│   ├── notificar_partidos.py # Script unificado de notificaciones
│   └── iniciar_notificaciones_mejoradas.py # Iniciar notificaciones
├── tests/                  # Scripts de prueba
│   ├── test_datos_locales.py # Prueba con datos locales
│   ├── test_partido_pasado.py # Prueba con partido pasado
│   └── test_telegram_simple.py # Prueba simple de Telegram
├── data/                   # Datos y ejemplos
│   ├── ejemplos/           # Datos de ejemplo para pruebas
│   └── liga_mx_matches.json # Datos de partidos
├── utils/                  # Utilidades adicionales
├── .gitignore              # Archivos ignorados por git
└── requirements.txt        # Dependencias del proyecto
```

## Configuración de Credenciales

Para configurar las credenciales del bot, crea un archivo `.env` en la raíz del proyecto con el siguiente formato:

```
LIVESCORE_API_KEY=tu_api_key_aqui
LIVESCORE_API_SECRET=tu_api_secret_aqui
TELEGRAM_BOT_TOKEN=tu_token_de_bot_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
LIGA_MX_COMPETITION_ID=45
```

> **IMPORTANTE**: Nunca compartas tus credenciales ni las incluyas en el control de versiones. El archivo `.env` está incluido en `.gitignore` para evitar que se suba accidentalmente.

## Uso

### Notificar partidos

```bash
# Notificar partidos de toda la semana
python scripts/notificar_partidos.py --tipo semana

# Notificar partidos del fin de semana (viernes a domingo)
python scripts/notificar_partidos.py --tipo finde

# Notificar partidos de la jornada actual
python scripts/notificar_partidos.py --tipo jornada
```

### Iniciar notificaciones en tiempo real

```bash
python scripts/iniciar_notificaciones_mejoradas.py
```

### Pruebas

```bash
# Prueba simple de Telegram
python tests/test_telegram_simple.py

# Prueba con datos locales
python tests/test_datos_locales.py

# Prueba con partido pasado
python tests/test_partido_pasado.py
```

## Dependencias

- Python 3.6+
- requests
- pytz
- asyncio

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Notas

- Todas las fechas y horas se muestran en la zona horaria de México (Ciudad de México)
- Las notificaciones se envían en español
- El bot monitorea partidos en vivo cada 30 segundos
