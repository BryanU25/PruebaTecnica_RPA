import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# --- Crear carpeta de logs si no existe ---
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# --- Formatos de logging ---
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# --- Configuración de rotación ---
MAX_BYTES = 5_000_000  # 5 MB por archivo
BACKUP_COUNT = 3        # Mantiene 3 versiones antiguas (app.log.1, app.log.2...)


def configurar_logs_generales():
    """
    Configura el logger global para toda la aplicación.
    - app.log: contiene todos los eventos (INFO, WARNING, ERROR)
    - error.log: solo errores (ERROR y CRITICAL)
    - también imprime todo en consola
    """

    # Eliminar handlers previos del root logger
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # --- Handler principal: app.log ---
    app_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # --- Handler de errores: error.log ---
    error_handler = RotatingFileHandler(
        LOG_DIR / "error.log",
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # --- Handler para consola ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # --- Configurar logger raíz ---
    logging.basicConfig(
        level=logging.INFO,
        handlers=[app_handler, error_handler, console_handler]
    )

    logging.info("✅ Configuración de logs generales inicializada.")
    logging.info("📄 app.log y error.log con rotación activa.")


def configurar_logger_automatizacion():
    """
    Crea un logger independiente para el módulo de automatización.
    Guarda sus registros en logs/automatizacion.log y también muestra en consola.
    También reenvía errores al archivo global error.log.
    """
    logger = logging.getLogger("automatizador")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Evita duplicados en el logger raíz

    # --- Handler de archivo rotativo (automatización) ---
    auto_handler = RotatingFileHandler(
        LOG_DIR / "automatizacion.log",
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    auto_handler.setLevel(logging.INFO)
    auto_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # --- Handler de errores (error.log global) ---
    error_handler = RotatingFileHandler(
        LOG_DIR / "error.log",
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # --- Handler para consola ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # --- Limpiar handlers previos ---
    if logger.hasHandlers():
        logger.handlers.clear()

    # --- Añadir handlers ---
    logger.addHandler(auto_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    logger.info("🧭 Logger de automatización configurado correctamente.")
    logger.info("📄 automatizacion.log y error.log con rotación activa.")
    return logger