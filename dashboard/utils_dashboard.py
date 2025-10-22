from pathlib import Path
import json
from typing import List, Dict, Optional, Tuple
import datetime as dt

# Patrón de archivo esperado: resultado_general_YYYYMMDD_HHMMSS.json
FILENAME_PREFIX = "resultado_general_"
FILENAME_SUFFIX = ".json"


def _data_dir() -> Path:
    # /dashboard/utils_dashboard.py -> Sube dos niveles hasta la raíz del proyecto y entra a /data
    return Path(__file__).resolve().parents[1] / "data"


def list_json_results() -> List[Path]:
    """Lista los archivos resultado_general_*.json en /data."""
    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return sorted(data_dir.glob(f"{FILENAME_PREFIX}*{FILENAME_SUFFIX}"))


def _parse_timestamp_from_name(path: Path) -> Optional[dt.datetime]:
    """
    Intenta extraer el timestamp del nombre: resultado_general_YYYYMMDD_HHMMSS.json
    Devuelve None si no calza el patrón.
    """
    name = path.name
    try:
        stem = name.removeprefix(FILENAME_PREFIX).removesuffix(FILENAME_SUFFIX)
        
        date_str, time_str = stem.split("_", 1)
        return dt.datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
    except Exception:
        return None


def pick_latest_file(paths: List[Path]) -> Optional[Path]:
    """
    Selecciona el archivo más reciente priorizando el timestamp del nombre.
    Si no puede parsearlo, usa la hora de modificación (mtime) como fallback.
    """
    if not paths:
        return None

    # Ordena por: (1) timestamp parseado si existe, (2) mtime
    def sort_key(p: Path) -> Tuple[dt.datetime, float]:
        ts = _parse_timestamp_from_name(p)
        # Si no hay timestamp en nombre, usa época 1970 para que no "gane"
        ts_name = ts or dt.datetime(1970, 1, 1)
        return (ts_name, p.stat().st_mtime)

    return sorted(paths, key=sort_key, reverse=True)[0]


def load_json(path: Path) -> List[Dict]:
    """
    Carga un JSON de resultados (lista de ciudades).
    Lanza ValueError con mensaje claro si hay problema.
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("El archivo no contiene una lista de resultados por ciudad.")
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido en {path.name}: {e}") from e
    except FileNotFoundError:
        raise ValueError(f"No se encontró el archivo: {path}")
    except Exception as e:
        raise ValueError(f"Error al leer {path.name}: {e}") from e
