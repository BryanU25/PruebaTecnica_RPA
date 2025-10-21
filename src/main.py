import json
import api_clima as ac
import api_divisas as ad
import api_tempo as at
import procesar_clima as pc 
from pathlib import Path
from tenacity import RetryError
import logging

logging.basicConfig(
    filename="logs/app.log",          # Archivo donde se guardan los logs
    level=logging.INFO,               # Nivel: DEBUG, INFO, WARNING, ERROR
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

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

         # Guardar resultados parciales (aunque alguno sea None)
        resultados.append({
            "ciudad": nombre,
            "clima": datos_clima["clima"] if datos_clima else None,
            "finanzas": datos_divisas if datos_divisas else None,
            "tiempo": datos_tiempo if datos_tiempo else None
        })

    # Al final, guardar un resumen general
    ruta = Path(__file__).parent.parent / "data" / "resultado_general.json"
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=4, ensure_ascii=False)

    print("\n✅ Proceso completado. Datos guardados en /data/resultado_general.json")

if __name__ == "__main__":
    main()
