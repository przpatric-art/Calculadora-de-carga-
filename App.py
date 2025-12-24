import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Inventario Permanente", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
# REEMPLAZA ESTA URL POR LA TUVA:
URL_DE_TU_HOJA = "AQUÍ_PEGA_TU_LINK_DE_GOOGLE_SHEETS"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- INICIALIZACIÓN DE INVENTARIO (MEMORIA DE SESIÓN) ---
if 'inventario' not in st.session_state:
    st.session_state.inventario = {
        f"Losa {i+1}": {f"Lote {j+1}": 0.0 for j in range(6)} for i in range(7)
    }

st.title("🚜 Sistema de Inventario con Respaldo en Google Sheets")

# --- FUNCIONES DE GUARDADO ---
def guardar_en_gsheets(datos):
    try:
        # Leer datos actuales
        df_existente = conn.read(spreadsheet=URL_DE_TU_HOJA)
        # Crear nuevo registro
        nuevo_df = pd.DataFrame([datos])
        # Combinar y escribir
        df_final = pd.concat([df_existente, nuevo_df], ignore_index=True)
        conn.update(spreadsheet=URL_DE_TU_HOJA, data=df_final)
        return True
    except:
        return False

# --- ITEM 1: INGRESO DE CARGA ---
with st.expander("📥 REGISTRAR INGRESO DE CARGA"):
    col1, col2, col3 = st.columns(3)
    with col1:
        losa_sel = st.selectbox("Losa", [f"Losa {i+1}" for i in range(7)])
    with col2:
        lote_sel = st.selectbox("Lote", [f"Lote {j+1}" for j in range(6)])
    with col3:
        cantidad = st.number_input("Toneladas", min_value=0.0, step=1.0)
    
    if st.button("Confirmar Ingreso"):
        st.session_state.inventario[losa_sel][lote_sel] += cantidad
        registro = {
            "Fecha/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Tipo": "INGRESO",
            "Ubicación": f"{losa_sel}-{lote_sel}",
            "Movimiento": f"+{cantidad}",
            "Saldo Final": st.session_state.inventario[losa_sel][lote_sel]
        }
        if guardar_en_gsheets(registro):
            st.success("Guardado en Google Sheets")
        else:
            st.error("Error al conectar con la hoja")

# --- ITEM 2: DESPACHO ---
st.divider()
st.subheader("📤 Registro de Salida")
c1, c2, c3, c4 = st.columns(4)
with c1:
    l_out = st.selectbox("Losa origen", [f"Losa {i+1}" for i in range(7)], key="lo")
with c2:
    lt_out = st.selectbox("Lote origen", [f"Lote {j+1}" for j in range(6)], key="lto")
with c3:
    balde = st.number_input("Peso Balde", value=3.5)
with c4:
    n_paladas = st.number_input("Paladas", min_value=0)

salida_total = n_paladas * balde

if st.button("Registrar Salida"):
    if st.session_state.inventario[l_out][lt_out] >= salida_total:
        st.session_state.inventario[l_out][lt_out] -= salida_total
        registro = {
            "Fecha/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Tipo": "SALIDA",
            "Ubicación": f"{l_out}-{lt_out}",
            "Movimiento": f"-{salida_total}",
            "Saldo Final": st.session_state.inventario[l_out][lt_out]
        }
        guardar_en_gsheets(registro)
        st.warning(f"Despachado: {salida_total} Ton")
    else:
        st.error("Stock insuficiente")

# --- VISUALIZACIÓN ---
st.divider()
st.write("### Estado de Stock por Losa")
for i in range(0, 7, 4):
    cols = st.columns(4)
    for j in range(4):
        idx = i + j
        if idx < 7:
            with cols[j]:
                nombre = f"Losa {idx+1}"
                st.write(f"**{nombre}**")
                st.table(pd.DataFrame.from_dict(st.session_state.inventario[nombre], orient='index'))

# --- HISTORIAL DESDE GOOGLE SHEETS ---
st.divider()
st.subheader("📜 Historial Permanente (Google Sheets)")
try:
    df_historial = conn.read(spreadsheet=https://docs.google.com/spreadsheets/d/19uJo5QXVub5O9XeYMi-n37Dynnushv--CFTG2IajBho/edit?usp=drivesdk
    st.dataframe(df_historial.tail(10), use_container_width=True)
except:
    st.info("Conectando con la base de datos...")
