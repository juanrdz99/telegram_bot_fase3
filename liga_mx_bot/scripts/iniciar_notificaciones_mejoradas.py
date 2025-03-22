"""
Script para iniciar el sistema mejorado de notificaciones de partidos de Liga MX
"""
import asyncio
import logging
import signal
import sys
import os

# Agregar el directorio raíz al path para poder importar los módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.enhanced_match_tracker import EnhancedMatchTracker

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variable para controlar el bucle principal
running = True

def signal_handler(sig, frame):
    """Manejador de señales para detener el programa correctamente"""
    global running
    logger.info("Recibida señal de interrupción, deteniendo el programa...")
    running = False

async def main():
    """Función principal"""
    global running
    
    # Registrar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("Iniciando sistema mejorado de notificaciones de Liga MX...")
    
    # Crear instancia del rastreador mejorado
    tracker = EnhancedMatchTracker()
    
    # Intervalo de verificación en segundos
    check_interval = 30
    
    try:
        # Mostrar mensaje de inicio
        print("\n")
        print("=" * 80)
        print("  SISTEMA MEJORADO DE NOTIFICACIONES DE LIGA MX INICIADO")
        print("  Presiona Ctrl+C para detener")
        print("=" * 80)
        print("\n")
        
        # Verificar partidos inmediatamente al inicio
        await tracker.check_upcoming_matches()
        await tracker.check_live_matches()
        
        # Bucle principal
        while running:
            # Verificar próximos partidos
            await tracker.check_upcoming_matches()
            
            # Verificar partidos en vivo
            await tracker.check_live_matches()
            
            # Esperar antes de la próxima verificación
            for _ in range(check_interval):
                if not running:
                    break
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("Interrupción de teclado detectada, deteniendo el programa...")
    except Exception as e:
        logger.error(f"Error en el bucle principal: {e}")
    finally:
        logger.info("Sistema de notificaciones detenido")
        print("\n")
        print("=" * 80)
        print("  SISTEMA DE NOTIFICACIONES DETENIDO")
        print("=" * 80)
        print("\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Programa detenido por el usuario")
    sys.exit(0)
