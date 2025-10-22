import streamlit as st
from pathlib import Path
from typing import List, Dict, Optional
from utils_dashboard import list_json_results, pick_latest_file, load_json

st.set_page_config(
    page_title="Dashboard Prueba Técnica - Mission SAS",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard – Prueba Técnica (Mission SAS)")
st.caption("Etapa 3: Carga del archivo JSON más reciente desde /data")

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

colA, colB = st.columns([1, 2])
with colA:
    st.metric("Archivo seleccionado", selected_path.name)
with colB:
    st.caption(f"Ruta: `{selected_path}`")

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

st.success("✅ Datos cargados correctamente.")
st.write(f"Ciudades encontradas: **{len(data)}**")

# ------------------------------------------------------------
# 🔹 Selector de ciudad (sidebar)
# ------------------------------------------------------------
st.sidebar.header("🏙️ Seleccionar ciudad")

# Obtener lista de nombres únicos
ciudades_disponibles = [c["ciudad"] for c in data if "ciudad" in c]
if not ciudades_disponibles:
    st.error("No se encontraron nombres de ciudades en el archivo cargado.")
    st.stop()

ciudad_seleccionada = st.sidebar.selectbox(
    "Ciudad:",
    options=ciudades_disponibles,
    index=0,
    help="Selecciona la ciudad para ver sus métricas y alertas."
)

# Obtener los datos de la ciudad seleccionada
ciudad_data = next((c for c in data if c["ciudad"] == ciudad_seleccionada), None)
if ciudad_data is None:
    st.error("No se pudo cargar la información de la ciudad seleccionada.")
    st.stop()

st.divider()
st.subheader(f"🌆 Datos actuales para **{ciudad_seleccionada}**")

# ------------------------------------------------------------
# 📊 Métricas principales (IVV, Nivel de riesgo, Motivo)
# ------------------------------------------------------------

ivv_info = ciudad_data.get("componentes_ivv", {})
ivv_score = ciudad_data.get("ivv_score", None)
nivel = ciudad_data.get("nivel_riesgo", "DESCONOCIDO")
color = ciudad_data.get("color", "#6c757d")
motivo = ciudad_data.get("motivo", None)

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    st.metric(
        label="IVV (Índice de Viabilidad de Viaje)",
        value=f"{ivv_score if ivv_score is not None else '—'}",
        delta=None,
        help="Índice ponderado entre clima, divisas y radiación UV (0-100)."
    )

with col2:
    st.markdown(
        f"""
        <div style="text-align:center; padding:0.5em;
                    border-radius:8px; background-color:{color}; color:white;">
            <b>Nivel de riesgo:</b><br>{nivel}
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    if motivo:
        st.warning(f"ℹ️ **Motivo:** {motivo}")
    else:
        st.success("✅ Datos completos para el cálculo del IVV.")

st.markdown("#### 🔍 Componentes del IVV")


if ivv_info:
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("🌤️ Clima", ivv_info.get("clima_score", "—"))
    col_b.metric("💱 Divisas", ivv_info.get("cambio_score", "—"))
    col_c.metric("☀️ UV", ivv_info.get("uv_score", "—"))
else:
    st.info("No hay datos de componentes IVV disponibles para esta ciudad.")

# # Vista previa rápida (limitada) para confirmar estructura
# with st.expander("Vista previa del JSON (primeras 2 ciudades)"):
#     st.json(data[:2])

# st.divider()
# st.info(
#     "✅ Paso 1 completado: carga del JSON lista.\n\n"
#     "Siguiente paso: **selector de ciudad en la barra lateral** y construcción de "
#     "**métricas dinámicas (IVV, riesgo, motivo)**."
# )
