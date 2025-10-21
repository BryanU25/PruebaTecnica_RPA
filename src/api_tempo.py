import requests
import logging
from tenacity import retry, stop_after_attempt, wait_fixed
from datetime import datetime


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def obtener_zona_horaria(timezone_objetivo):
    """ Obtiene la hora local actual y la diferencia con Bogotá usando WorldTimeAPI."""
    try:
        # Consultar hora local de la ciudad objetivo
        url_ciudad = f"http://worldtimeapi.org/api/timezone/{timezone_objetivo}"
        resp_ciudad = requests.get(url_ciudad, timeout=10)
        resp_ciudad.raise_for_status()
        data_ciudad = resp_ciudad.json()

        # Consultar hora de Bogotá
        url_bogota = "http://worldtimeapi.org/api/timezone/America/Bogota"
        resp_bogota = requests.get(url_bogota, timeout=10)
        resp_bogota.raise_for_status()
        data_bogota = resp_bogota.json()

        # Extraer datetime
        hora_ciudad = datetime.fromisoformat(data_ciudad["datetime"].replace("Z", "+00:00"))
        hora_bogota = datetime.fromisoformat(data_bogota["datetime"].replace("Z", "+00:00"))

        # Calcular diferencia horaria (en horas)
        diferencia = (hora_ciudad - hora_bogota).total_seconds() / 3600

        logging.info(f"Zona horaria obtenida correctamente para {timezone_objetivo}")

        return {
            "timezone": timezone_objetivo,
            "hora_local": data_ciudad["datetime"],
            "diferencia_horaria_con_bogota": round(diferencia, 1)
        }

    except requests.exceptions.RequestException as e:
        logging.error(f"Error de conexión con WorldTimeAPI ({timezone_objetivo}): {e}")
        raise

    except KeyError as e:
        logging.error(f"Campo faltante en respuesta WorldTimeAPI: {e}")
        raise

    except Exception as e:
        logging.error(f"Error general en obtención de zona horaria ({timezone_objetivo}): {e}")
        raise
