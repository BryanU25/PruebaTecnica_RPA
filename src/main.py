import json
from pathlib import Path
import api_clima as ac
import procesar_clima as pc
import api_divisas as ad


def cargar_config():
    ruta_config = Path(__file__).parent.parent / "config" / "config.json"
    with open(ruta_config, "r", encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    config = cargar_config()
    ciudad = config["ciudades"][1]  # Nueva York

    print(f"Consultando clima de {ciudad['nombre']}...")
    
    datos_clima_raw = ac.obtener_datos_clima(ciudad["lat"], ciudad["lon"])
    datos_clima = pc.transformar_datos_clima(datos_clima_raw, ciudad)
    print("Datos clima:",json.dumps(datos_clima, sort_keys=True, indent=4))
    

    print(f"Consultando tipo de cambio para {ciudad['nombre']} ({ciudad['moneda']})...")
    datos_divisas = ad.obtener_tipo_cambio(ciudad["moneda"])

    print("Resultado de finanzas:",json.dumps(datos_divisas, sort_keys=True, indent=4))
