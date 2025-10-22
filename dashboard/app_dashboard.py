import streamlit as st
import plotly.express as px
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from utils_dashboard import list_json_results, pick_latest_file, load_json

st.set_page_config(
    page_title="Dashboard Prueba Técnica - Mission SAS",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard – Prueba Técnica (Mission SAS)")

# ---------- Helpers con caché ----------
@st.cache_data(show_spinner=False)
def cached_list_files() -> List[Path]:
    return list_json_results()

@st.cache_data(show_spinner=True)
def cached_load_json(path: Path) -> List[Dict]:
    return load_json(path)


# ---------- UI de carga ----------
st.sidebar.header("📁 Fuente de datos")
files = cached_list_files()

if not files:
    st.error("No se encontraron archivos en /data con el patrón `resultado_general_*.json`.")
    st.info("Asegúrate de ejecutar el automatizador para generar archivos versionados.")
    st.stop()

# Selector manual (útil para pruebas) y opción 'más reciente'
latest = pick_latest_file(files)
latest_label = latest.name if latest else "—"

option = st.sidebar.selectbox(
    "Seleccionar archivo",
    options=["(usar el más reciente)"] + [p.name for p in files],
    index=0,
    help="Puedes elegir un archivo específico para depurar o usar siempre el más reciente."
)

if option == "(usar el más reciente)":
    selected_path = latest
else:
    selected_path = next((p for p in files if p.name == option), latest)

if selected_path is None:
    st.error("No se pudo determinar el archivo más reciente.")
    st.stop()

# ------------------------------------------------------------
# 📅 Mostrar información legible del registro cargado
# ------------------------------------------------------------
from datetime import datetime

def formatear_nombre_archivo(nombre: str) -> str:
    """
    Convierte el nombre del archivo JSON en un título legible.
    Ejemplo: resultado_general_20251021_150400.json → Registro del 2025-10-21 a las 15:04:00
    """
    try:
        base = nombre.replace("resultado_general_", "").replace(".json", "")
        fecha_str, hora_str = base.split("_")
        fecha = datetime.strptime(f"{fecha_str}{hora_str}", "%Y%m%d%H%M%S")
        return f"Registro del {fecha.strftime('%Y-%m-%d')} a las {fecha.strftime('%H:%M:%S')}"
    except Exception:
        return "Registro sin formato reconocido"

# Mostrar título en formato natural

st.subheader(formatear_nombre_archivo(selected_path.name))

# ---------- Cargar datos ----------
try:
    data = cached_load_json(selected_path)
except ValueError as e:
    st.error(f"Error al cargar el archivo: {e}")
    st.stop()

# Validación mínima de esquema esperado (campos clave por ciudad)
required_city_keys = {"ciudad", "componentes_ivv", "clima", "finanzas", "tiempo", "alertas"}
missing = []
for i, item in enumerate(data):
    if not isinstance(item, dict):
        missing.append((i, "no es un dict"))
        continue
    faltantes = required_city_keys - set(item.keys())
    if faltantes:
        missing.append((i, f"faltan claves: {', '.join(sorted(faltantes))}"))

if missing:
    st.warning(
        "El archivo cargado no cumple el esquema esperado en algunos elementos. "
        "Revisa `logs/app.log` y la generación de `resultado_general_*.json`."
    )
    with st.expander("Detalles del esquema faltante"):
        for idx, msg in missing[:20]:
            st.write(f"• Elemento {idx}: {msg}")


# ------------------------------------------------------------
#  Resumen general de métricas por ciudad
# ------------------------------------------------------------
st.divider()
st.subheader("🌆 Resumen general de métricas por ciudad")

# Extraer métricas relevantes de cada ciudad
filas = []
for c in data:
    ciudad = c.get("ciudad", "—")
    clima = c.get("clima", {})
    fin = c.get("finanzas", {})
    ivv = c.get("ivv_score")
    nivel = c.get("nivel_riesgo", "DESCONOCIDO")
    color = c.get("color", "#6c757d")

    filas.append({
        "Ciudad": ciudad,
        "Temperatura (°C)": clima.get("temperatura_actual", "—"),
        "Viento (km/h)": clima.get("viento", "—"),
        "UV": clima.get("uv", "—"),
        "Precipitación (%)": clima.get("precipitacion", "—"),
        "Tipo de cambio": fin.get("tipo_cambio_actual", "—"),
        "Variación diaria (%)": fin.get("variacion_diaria", "—"),
        "Tendencia": fin.get("tendencia_5_dias", "—"),
        "IVV Score": ivv if ivv is not None else "—",
        "Nivel de riesgo": nivel,
        "color": color
    })


df_resumen = pd.DataFrame(filas)

if df_resumen.empty:
    st.info("No se encontraron datos para generar la tabla resumen.")
else:
    # Crear copia sin columna de color (solo para estilo)
    df_vista = df_resumen.drop(columns=["color"])

    # Aplicar estilo de color por nivel de riesgo
    styled_df = (
        df_vista.style
        .apply(
            lambda s: [
                f"background-color: {df_resumen.loc[i, 'color']}; color: white; text-align:center;"
                if s.name == "Nivel de riesgo" else ""
                for i in s.index
            ],
            axis=0
        )
        .format(precision=2, na_rep="—")
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )

# ------------------------------------------------------------
#  Gráfico de temperatura (pronóstico 7 días)
# ------------------------------------------------------------
st.markdown("### 🌤️ Pronóstico de temperatura (7 días)")

# Crear selector de ciudad integrado en esta sección
ciudades_disponibles = [c["ciudad"] for c in data if "ciudad" in c]
if not ciudades_disponibles:
    st.warning("No hay ciudades disponibles para mostrar el pronóstico.")
else:
    col_sel1, col_sel2 = st.columns([1.5, 3])
    with col_sel1:
        ciudad_seleccionada = st.selectbox(
            "Selecciona una ciudad:",
            options=ciudades_disponibles,
            index=0,
            help="Cambia la ciudad para actualizar el pronóstico de temperatura."
        )

    # Filtrar datos de la ciudad seleccionada
    ciudad_data = next((c for c in data if c["ciudad"] == ciudad_seleccionada), None)
    clima = ciudad_data.get("clima", {}) if ciudad_data else {}
    pronostico = clima.get("pronostico_7_dias", [])

    if pronostico and isinstance(pronostico, list):
        # Crear DataFrame
        df_temp = pd.DataFrame(pronostico)

        # Asegurar formato correcto
        if {"fecha", "temp_max", "temp_min"} <= set(df_temp.columns):
            df_temp["fecha"] = pd.to_datetime(df_temp["fecha"], errors="coerce")

            fig_temp = px.line(
                df_temp,
                x="fecha",
                y=["temp_max", "temp_min"],
                labels={"value": "Temperatura (°C)", "variable": "Medición"},
                title=f"Tendencia de temperatura – {ciudad_seleccionada}",
                markers=True
            )

            fig_temp.update_layout(
                legend_title_text="Tipo",
                hovermode="x unified",
                xaxis_title="Fecha",
                yaxis_title="Temperatura (°C)",
                template="plotly_white",
                height=400
            )

            st.plotly_chart(fig_temp, use_container_width=True)
        else:
            st.warning("Los datos de pronóstico no tienen el formato esperado (fecha, temp_max, temp_min).")
    else:
        st.info("No se encontraron datos de pronóstico de temperatura para esta ciudad.")

# ------------------------------------------------------------
#  Comparativo general de tipo de cambio por ciudad
# ------------------------------------------------------------
st.markdown("### 💱 Comparativo general de tipo de cambio actual (USD → moneda local)")

# Crear lista de datos agregados de todas las ciudades
ciudades = []
tipos_cambio = []
variaciones = []

for entry in data:
    nombre = entry.get("ciudad")
    fin = entry.get("finanzas", {})
    if fin and "tipo_cambio_actual" in fin:
        ciudades.append(nombre)
        tipos_cambio.append(fin["tipo_cambio_actual"])
        variaciones.append(fin.get("variacion_diaria", 0))

if not ciudades:
    st.info("No hay datos de tipo de cambio disponibles para generar el comparativo.")
else:
    df_comparativo = pd.DataFrame({
        "Ciudad": ciudades,
        "Tipo de cambio": tipos_cambio,
        "Variación (%)": variaciones
    })

    # Crear gráfico de barras horizontales
    fig_bar = px.bar(
        df_comparativo,
        x="Tipo de cambio",
        y="Ciudad",
        orientation="h",
        color="Variación (%)",
        color_continuous_scale="RdYlGn",
        text="Tipo de cambio",
        title="Tipo de cambio actual por ciudad (USD → moneda local)"
    )

    fig_bar.update_traces(
        texttemplate="%{text:.3f}",
        textposition="outside"
    )

    fig_bar.update_layout(
        xaxis_title="Tipo de cambio",
        yaxis_title="Ciudad",
        coloraxis_colorbar=dict(title="Variación diaria (%)"),
        template="plotly_white",
        height=450,
        margin=dict(l=80, r=40, t=60, b=40)
    )

    st.plotly_chart(fig_bar, use_container_width=True)

# ------------------------------------------------------------
# Resumen general de alertas (todas las ciudades)
# ------------------------------------------------------------
st.divider()
st.markdown("### ⚠️ Resumen general de alertas")

# Recolectar todas las alertas del JSON
todas_alertas = []
for c in data:
    ciudad = c.get("ciudad", "—")
    for alerta in c.get("alertas", []):
        alerta["ciudad"] = ciudad
        todas_alertas.append(alerta)

if not todas_alertas:
    st.success("✅ No hay alertas activas en ninguna ciudad.")
else:
    # Ordenar por severidad (ALTA > MEDIA > BAJA)
    orden_severidad = {"ALTA": 3, "MEDIA": 2, "BAJA": 1}
    todas_alertas = sorted(
        todas_alertas,
        key=lambda a: orden_severidad.get(a.get("severidad", "BAJA"),0),
        reverse=True
    )

    # Mostrar alertas agrupadas por ciudad
    for alerta in todas_alertas:
        tipo = alerta.get("tipo", "DESCONOCIDO")
        severidad = alerta.get("severidad", "BAJA").upper()
        mensaje = alerta.get("mensaje", "Sin descripción")
        ciudad = alerta.get("ciudad", "—")

        # Definir color e ícono según severidad
        if severidad == "ALTA":
            color = "#dc3545"  # rojo
            icono = "🚨"
        elif severidad == "MEDIA":
            color = "#fd7e14"  # naranja
            icono = "⚠️"
        else:
            color = "#ffc107"  # amarillo
            icono = "ℹ️"

        # Contenedor visual con información de ciudad
        st.markdown(
            f"""
            <div style='background-color:{color}20;
                        border-left:6px solid {color};
                        padding:0.7em 1em;
                        margin-bottom:0.6em;
                        border-radius:8px'>
                <b style='color:{color}; font-size:1.05em;'>{icono} {tipo} — {severidad}</b>
                <span style='float:right; color:#555;'>🌆 {ciudad}</span><br>
                <span style='color:#333;'>{mensaje}</span>
            </div>
            """,
            unsafe_allow_html=True
        )


# ------------------------------------------------------------
# Mapa general de ciudades por nivel de riesgo
# ------------------------------------------------------------
st.divider()
st.markdown("### 🌍 Mapa general de riesgo (IVV por ciudad)")

# Crear DataFrame con todas las ciudades y sus coordenadas + riesgo
ciudades_mapa = []
for c in data:
    info_ivv = c.get("componentes_ivv", {})
    clima = c.get("clima", {})
    ciudad_conf = next(
        (conf for conf in data if conf.get("ciudad") == c["ciudad"]), None
    )

    ciudades_mapa.append({
        "ciudad": c.get("ciudad"),
        "ivv_score": c.get("ivv_score"),
        "nivel_riesgo": c.get("nivel_riesgo", "DESCONOCIDO"),
        "color": c.get("color", "#6c757d"),
    })

# Si las coordenadas no están incluidas en el JSON, las obtendremos desde config.json
# Cargar config si no hay coordenadas en los datos
if all(c.get("lat") is None for c in ciudades_mapa):
    from pathlib import Path
    import json
    ruta_config = Path(__file__).parent.parent / "config" / "config.json"
    with open(ruta_config, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    coords = {c["nombre"]: (c["lat"], c["lon"]) for c in config_data["ciudades"]}

    for c in ciudades_mapa:
        if c["ciudad"] in coords:
            c["lat"], c["lon"] = coords[c["ciudad"]]

# Filtrar las ciudades con coordenadas válidas
df_mapa = pd.DataFrame([c for c in ciudades_mapa if c["lat"] is not None and c["lon"] is not None])

if df_mapa.empty:
    st.info("No se pudieron determinar coordenadas para generar el mapa.")
else:
    # Convertir colores hex a categoría según nivel
    color_map = {
        "BAJO": "#28a745",
        "MEDIO": "#ffc107",
        "ALTO": "#fd7e14",
        "CRITICO": "#dc3545",
        "DESCONOCIDO": "#6c757d"
    }

    df_mapa["color"] = df_mapa["nivel_riesgo"].map(color_map).fillna("#6c757d")

    fig_map = px.scatter_mapbox(
        df_mapa,
        lat="lat",
        lon="lon",
        size="ivv_score",
        color="nivel_riesgo",
        color_discrete_map=color_map,
        hover_name="ciudad",
        hover_data={
            "nivel_riesgo": True,
            "ivv_score": True,
            "lat": False,
            "lon": False
        },
        zoom=1,
        height=500,
        title="Mapa mundial de riesgo (IVV por ciudad)"
    )

    fig_map.update_layout(
        mapbox_style="carto-positron",  # Alternativas: "open-street-map", "stamen-terrain", "white-bg"
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_showscale=False,
        legend=dict(
            title="Nivel de riesgo",
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="center",
            x=0.5
        )
    )

    st.plotly_chart(fig_map, use_container_width=True)
