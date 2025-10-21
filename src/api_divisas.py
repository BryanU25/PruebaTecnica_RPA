import requests
import random
import logging
from tenacity import retry, stop_after_attempt, wait_fixed


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def obtener_tipo_cambio(moneda_objetivo):
    """Obtiene el tipo de cambio USD → moneda_objetivo y simula 5 días de histórico."""
    url_base = "https://open.er-api.com/v6/latest/USD"

    try:
        respuesta = requests.get(url_base, timeout=10)
        respuesta.raise_for_status()
        data = respuesta.json()
        
        if "rates" not in data:
            raise ValueError("Estructura inesperada en respuesta de ExchangeRate API")

        tipo_cambio_actual = data["rates"].get(moneda_objetivo)

        if tipo_cambio_actual is None:
            raise ValueError(f"No se encontró tasa para {moneda_objetivo}")

        logging.info(f"Tipo de cambio obtenido correctamente para {moneda_objetivo}")

        # Generar histórico simulado ±2% en los últimos 5 días
        historico = [tipo_cambio_actual]
        valor = tipo_cambio_actual

        for _ in range(4):
            variacion = random.uniform(-0.02, 0.02)  # entre -2% y +2%
            valor = round(valor * (1 + variacion), 4)
            historico.append(valor)
            

        # Calcular variación diaria simulada (último día vs anterior)
        variacion_diaria = round(((historico[-1] - historico[-2]) / historico[-2]) * 100, 2)

        # --- Tendencia ---
        tendencia = analizar_tendencia(historico)

        return {
            # "moneda_objetivo": moneda_objetivo,
            "tipo_cambio_actual": tipo_cambio_actual,
            "variacion_diaria": variacion_diaria,
            "tendencia_5_dias": tendencia["tendencia"],
            # "historico": historico
        }

    except requests.exceptions.RequestException as e:
        logging.error(f"Error en conexión con ExchangeRate API: {e}")
        raise

    except ValueError as e:
        logging.error(f"Error en formato de respuesta o moneda: {e}")
        raise


def analizar_tendencia(historico):
    """Analiza una lista de valores y determina la tendencia."""
    direcciones = []
    for i in range(1, len(historico)):
        if historico[i] > historico[i - 1]:
            direcciones.append("up")
        elif historico[i] < historico[i - 1]:
            direcciones.append("down")
        else:
            direcciones.append("flat")

    # Contadores de rachas
    max_positiva = max_negativa = count_up = count_down = 0

    for d in direcciones:
        if d == "up":
            count_up += 1
            count_down = 0
            max_positiva = max(max_positiva, count_up)
        elif d == "down":
            count_down += 1
            count_up = 0
            max_negativa = max(max_negativa, count_down)
        else:
            count_up = count_down = 0

    # Determinar tendencia principal
    if max_positiva >= 3:
        tendencia = "positiva"
        dias = max_positiva
    elif max_negativa >= 3:
        tendencia = "negativa"
        dias = max_negativa
    else:
        tendencia = "estable"
        dias = 0

    return {
        "tendencia": tendencia,
        "dias_consecutivos": dias,
        "descripcion": (
            f"Tendencia {tendencia} durante {dias} días consecutivos"
            if dias > 0
            else "Tendencia estable sin rachas significativas"
        )
    }