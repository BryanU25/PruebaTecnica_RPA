import datetime
import logging
import json
from pathlib import Path


def transformar_datos_clima(data_api, nombre_ciudad):
    """Transforma los datos de Open-Meteo a una estructura uniforme."""
    try:
        clima = {}

        # Datos actuales
        clima["temperatura_actual"] = data_api["current"]["temperature_2m"]        
        clima["viento"] = data_api["current"]["wind_speed_10m"]
        clima["uv"] = data_api["current"]["uv_index"]
        clima["precipitacion"] = data_api["current"]["precipitation_probability"]

        # Datos diarios (7 días)
        pronostico_7_dias = []
        daily = data_api["daily"]

        fechas = daily["time"]
        temp_max = daily["temperature_2m_max"]
        temp_min = daily["temperature_2m_min"]
        

        for i in range(len(fechas)):
            pronostico_7_dias.append({
                "fecha": fechas[i],
                "temp_max": temp_max[i],
                "temp_min": temp_min[i],                
            })

        clima["pronostico_7_dias"] = pronostico_7_dias
        
        logging.info(f"Datos climáticos transformados correctamente para {nombre_ciudad}")
        return {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),            
            "ciudad": nombre_ciudad,
            "clima": clima
        }

    except KeyError as e:
        logging.error(f"Campo faltante en datos de clima: {e}")
        raise

    except Exception as e:
        logging.error(f"Error general transformando datos de clima: {e}")
        raise


def guardar_datos(data, nombre_archivo):
    ruta = Path(__file__).parent.parent / "data" / nombre_archivo
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)