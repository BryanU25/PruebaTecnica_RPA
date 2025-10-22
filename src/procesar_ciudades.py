import logging

def evaluar_alertas(ciudad, datos_clima, datos_finanzas):
    """
    Evalúa las alertas climáticas y financieras para una ciudad.
    Retorna una lista de alertas activas.
    """
    alertas = []

    # --- Alerta climática crítica ---
    if datos_clima:
        temp = datos_clima["clima"]["temperatura_actual"]
        viento = datos_clima["clima"]["viento"]
        lluvia = datos_clima["clima"]["precipitacion"]

        if temp > 35 or temp < 0:
            alertas.append({"tipo": "CLIMA", "severidad": "ALTA", "mensaje": f"Temperatura extrema ({temp}°C)"})
        if lluvia > 70:
            alertas.append({"tipo": "CLIMA", "severidad": "MEDIA", "mensaje": f"Alta probabilidad de lluvia ({lluvia}%)"})
        if viento > 50:
            alertas.append({"tipo": "CLIMA", "severidad": "MEDIA", "mensaje": f"Viento fuerte ({viento} km/h)"})

    # --- Alerta de tipo de cambio ---
    if datos_finanzas:
        variacion = datos_finanzas["variacion_diaria"]
        tendencia = datos_finanzas["tendencia_5_dias"]

        if abs(variacion) > 3:
            alertas.append({"tipo": "FINANZAS", "severidad": "ALTA", "mensaje": f"Variación de tipo de cambio > 3% ({variacion}%)"})
        if tendencia == "negativa":
            alertas.append({"tipo": "FINANZAS", "severidad": "BAJA", "mensaje": "Tendencia negativa en el tipo de cambio"})

    logging.info(f"Alertas evaluadas para {ciudad}: {len(alertas)} encontradas")
    return alertas


def calcular_ivv(datos_clima, datos_finanzas):
    """ 
    Calcula el Índice de Viabilidad de Viaje (IVV) según las reglas del negocio.  
    Si alguna fuente de datos está ausente, devuelve nivel 'DESCONOCIDO' e indica el motivo.
    """

    # --- Validar que haya datos de ambas fuentes ---
    if not datos_clima or not datos_finanzas:
        motivo = []
        if not datos_clima:
            motivo.append("Datos climáticos no disponibles")
        if not datos_finanzas:
            motivo.append("Datos financieros no disponibles")

        return {
            "ivv_score": None,
            "nivel_riesgo": "DESCONOCIDO",
            "color": "#6c757d", 
            "componentes_ivv": {},
            "motivo": " / ".join(motivo)
        }

    # --- Calcular componentes del IVV ---
    alertas_climaticas = 0
    temp = datos_clima["clima"]["temperatura_actual"]
    lluvia = datos_clima["clima"]["precipitacion"]
    viento = datos_clima["clima"]["viento"]

    # Criterios de alertas
    if temp > 35 or temp < 0: alertas_climaticas += 1
    if lluvia > 70: alertas_climaticas += 1
    if viento > 50: alertas_climaticas += 1

    clima_score = 100 - (alertas_climaticas * 25)

    cambio_score = 50 if abs(datos_finanzas["variacion_diaria"]) > 3 else 100
    uv = datos_clima["clima"]["uv"]

    if uv < 6:
        uv_score = 100
    elif 6 <= uv <= 8:
        uv_score = 75
    else:
        uv_score = 50

    ivv = (clima_score * 0.4) + (cambio_score * 0.3) + (uv_score * 0.3)
    ivv = round(ivv, 2)

    # Nivel de riesgo y color
    if ivv >= 80:
        nivel = "BAJO"
        color = "#28a745"
    elif ivv >= 60:
        nivel = "MEDIO"
        color = "#ffc107"
    elif ivv > 40:
        nivel = "ALTO"
        color = "#fd7e14"
    else:
        nivel = "CRITICO"
        color = "#dc3545"

    return {
        "ivv_score": ivv,
        "nivel_riesgo": nivel,
        "color": color, # Util para UI
        "componentes_ivv": {
            "clima_score": clima_score,
            "cambio_score": cambio_score,
            "uv_score": uv_score
        },
        "motivo": None
    }

def procesar_ciudad(ciudad, datos_clima, datos_finanzas, datos_tiempo):
    """
    Integra los datos de clima, finanzas y tiempo para una ciudad.
    Retorna un diccionario completo con alertas e IVV calculado.
    """
    alertas = evaluar_alertas(ciudad["nombre"], datos_clima, datos_finanzas)
    ivv_data = calcular_ivv(datos_clima, datos_finanzas)

    resultado = {
        "timestamp": datos_clima["timestamp"] if datos_clima else None,
        "ciudad": ciudad["nombre"],
        "clima": datos_clima["clima"] if datos_clima else None,
        "finanzas": datos_finanzas if datos_finanzas else None,
        "tiempo": datos_tiempo if datos_tiempo else None,
        "alertas": alertas,
        "ivv_score": ivv_data["ivv_score"],
        "nivel_riesgo": ivv_data["nivel_riesgo"],
        "componentes_ivv": ivv_data["componentes_ivv"],
        "color": ivv_data["color"],
        "motivo": ivv_data["motivo"]
    }

    logging.info(f"Ciudad procesada: {ciudad['nombre']} - IVV {ivv_data['ivv_score']}")
    return resultado
