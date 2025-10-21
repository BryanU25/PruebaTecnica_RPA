import requests
import logging
from tenacity import retry, stop_after_attempt, wait_fixed

logging.basicConfig(
    filename="logs/app.log",          # Archivo donde se guardan los logs
    level=logging.INFO,               # Nivel: DEBUG, INFO, WARNING, ERROR
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def obtener_datos_clima(lat, lon):
    """Consulta la API de Open-Meteo y retorna los datos relevantes."""
    url_base = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,        
        "current": "temperature_2m,wind_speed_10m,precipitation_probability,uv_index",
        # "hourly": "temperature_2m" #Maneja los mismos parametros que current pero por hora.
        "daily": "temperature_2m_max,temperature_2m_min",
        # "forecast_days": 7, #Esta por defecto en 7 días.
        "timezone": "auto"
    }  

    try:
        respuesta = requests.get(url_base, params=params, timeout=10)
        respuesta.raise_for_status() 

        data = respuesta.json()
        
        # Validar que la respuesta tenga los campos esperados
        if "current" not in data:
            raise ValueError("Estructura inesperada en la respuesta de la API.")

        logging.info(f"Datos climáticos obtenidos correctamente ({lat}, {lon})")
        return data

    except requests.exceptions.RequestException as e:
        logging.error(f"Error en la conexión con Open-Meteo: {e}")
        raise

    except ValueError as e:
        logging.error(f"Error en formato de respuesta: {e}")
        raise
