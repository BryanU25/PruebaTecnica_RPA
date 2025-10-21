import json
from pathlib import Path

def cargar_config():
    ruta_config = Path(__file__).parent.parent / "config" / "config.json"
    with open(ruta_config, "r", encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    config = cargar_config()
    print("Ciudades cargadas:")
    for ciudad in config["ciudades"]:
        print("-", ciudad["nombre"])
