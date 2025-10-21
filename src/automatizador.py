import time
import schedule
import datetime
from src.main import main
from config.config_logs  import configurar_logger_automatizacion

logger = configurar_logger_automatizacion()


def ejecutar_proceso():
    """ Ejecuta el flujo principal y guarda logs con control de versiones. """
    try:
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")        
        logger.info(f"🔄 Iniciando ejecución automática ({timestamp})")

        main()  # Ejecuta el proceso principal

        logger.info(f"✅ Ejecución completada correctamente ({timestamp})\n")

    except Exception as e:
        logger.error(f"❌ Error durante la ejecución automática: {e}")


def iniciar_automatizacion():
    """ Programa la ejecución automática cada 30 minutos. """
    # schedule.every(1).minutes.do(ejecutar_proceso)
    schedule.every(30).minutes.do(ejecutar_proceso)
    logger.info("🕒 Automatización iniciada. Ejecución cada 30 minutos.")

    # Bucle infinito para mantener el proceso corriendo
    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":
    iniciar_automatizacion()
