import time
import schedule
import datetime
import logging
from main import main


def ejecutar_proceso():
    """ Ejecuta el flujo principal y guarda logs con control de versiones. """
    try:
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")        
        logging.info(f"🔄 Iniciando ejecución automática ({timestamp})")

        main()  # Ejecuta el proceso principal

        logging.info(f"✅ Ejecución completada correctamente ({timestamp})\n")

    except Exception as e:
        logging.error(f"❌ Error durante la ejecución automática: {e}")


def iniciar_automatizacion():
    """ Programa la ejecución automática cada 30 minutos. """
    # schedule.every(1).minutes.do(ejecutar_proceso)
    schedule.every(30).minutes.do(ejecutar_proceso)
    logging.info("🕒 Automatización iniciada. Ejecución cada 30 minutos.")

    # Bucle infinito para mantener el proceso corriendo
    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":
    iniciar_automatizacion()
