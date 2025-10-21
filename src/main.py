import json
from src import api_clima as ac
from src import api_divisas as ad
from src import api_tempo as at
from src import procesar_clima as pc 
from src import procesar_ciudades as pz
import datetime
from pathlib import Path
from tenacity import RetryError
import logging
from config.config_logs import configurar_logs_generales

configurar_logs_generales()


def manejar_error_api(nombre_api, ciudad, error):
    """
    Maneja los errores de conexión o fallos en las APIs de forma centralizada.
    Retorna None para indicar que el módulo falló, pero no detiene el programa.
    """
    logging.error(f"[{nombre_api}] No se pudo obtener datos para {ciudad}: {error}")
    print(f"❌ {nombre_api}: Falló para {ciudad} tras varios intentos.")
    return None


def cargar_config():
    ruta_config = Path(__file__).parent.parent / "config" / "config.json"
    with open(ruta_config, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    
    config = cargar_config()
    resultados = []

    for ciudad in config["ciudades"]:
        nombre = ciudad["nombre"]
        print(f"\n🌍 Procesando ciudad: {nombre}")

        # --- Clima ---
        try:
            datos_clima_raw = ac.obtener_datos_clima(ciudad["lat"], ciudad["lon"])
            datos_clima = pc.transformar_datos_clima(datos_clima_raw, nombre)
        except RetryError as e:
            datos_clima = manejar_error_api("Open-Meteo", nombre, e)

        # --- Finanzas ---
        try:
            datos_divisas = ad.obtener_tipo_cambio(ciudad["moneda"])
        except RetryError as e:
            datos_divisas = manejar_error_api("ExchangeRate API", nombre, e)

        # --- Tiempo ---
        try:
            datos_tiempo = at.obtener_zona_horaria(ciudad["timezone"])
        except RetryError as e:
            datos_tiempo = manejar_error_api("WorldTimeAPI", nombre, e)

        # --- Combinar resultados (aunque alguno sea None) ---
        resultado_ciudad = pz.procesar_ciudad(ciudad, datos_clima, datos_divisas, datos_tiempo)
        resultados.append(resultado_ciudad)

    # print(json.dumps(resultados, sort_keys=True, indent=4))

     # --- Guardar resultado general con versiones ---
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    ruta = Path(__file__).parent.parent / "data" / f"resultado_general_{timestamp}.json"

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=4, ensure_ascii=False)

    print("\n✅ Proceso completado. Datos guardados en /data/resultado_general.json")

if __name__ == "__main__":
    main()