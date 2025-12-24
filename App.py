import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Gestión de Bodega Pro", layout="wide")

# --- CONFIGURACIÓN DE CONEXIÓN ---
# He guardado tu URL en esta variable para evitar errores de paréntesis más abajo
URL_DE_TU_HOJA = "https://docs.google.com/spreadsheets/d/19uJo5QXVub5O9XeYMi-n37Dynnushv--CFTG2IajBho/edit?usp=drivesdk"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- INICIALIZACIÓN DE DATOS (Memoria de Sesión) ---
if 'inventario' not in st.session_state:
    st.session_state.inventario = {
        f"Losa {i+1}": {f"Lote {j+1}": 0.0 for j in range(6)} for i in range(7)
    }

st.title("⚒️ Control de Inventario Permanente")

# --- FUNCIÓN PARA GUARDAR ---
def guardar_en_gsheets(datos):
    try:
        df_existente = conn.read(spreadsheet=URL_DE_TU_HOJA)
        nuevo_df = pd.DataFrame([datos])
        df_final = pd.concat([df_existente, nuevo_df], ignore_index=True)
        conn.update(spreadsheet=URL_DE_TU_HOJA, data=df_final)
        return True
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return False

# --- INTERFAZ DE ENTRADA Y SALIDA ---
col_izq, col_der = st.columns(2)

with col_izq:
    with st.expander("📥 REGISTRAR INGRESO"):
        l_in = st.selectbox("Losa", [f"Losa {i+1}" for i in range(7)], key="li")
        lt_in = st.selectbox("Lote", [f"Lote {j+1}" for j in range(6)], key="lti")
        cant_in = st.number_input("Toneladas a ingresar", min_value=0.0, step=1.0)
        if st.button("Confirmar Ingreso"):
            st.session_state.inventario[l_in][lt_in] += cant_in
            reg = {
                "Fecha/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Tipo": "INGRESO",
                "Ubicación": f"{l_in}-{lt_in}",
                "Movimiento": cant_in,
                "Saldo Final": st.session_state.inventario[l_in][lt_in]
            }
            guardar_en_gsheets(reg)
            st.success("Ingreso registrado")

with col_der:
    with st.expander("📤 REGISTRAR SALIDA"):
        l_out = st.selectbox("Losa", [f"Losa {i+1}" for i in range(7)], key="lo")
        lt_out = st.selectbox("Lote", [f"Lote {j+1}" for j in range(6)], key="lto")
        balde = st.number_input("Peso Balde (Ton)", value=3.5)
        paladas = st.number_input("Paladas", min_value=0)
        total_s = paladas * balde
        if st.button("Confirmar Salida"):
            if st.session_state.inventario[l_out][lt_out] >= total_s:
                st.session_state.inventario[l_out][lt_out] -= total_s
                reg = {
                    "Fecha/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "Tipo": "SALIDA",
                    "Ubicación": f"{l_out}-{lt_out}",
                    "Movimiento": -total_s,
                    "Saldo Final": st.session_state.inventario[l_out][lt_out]
                }
                guardar_en_gsheets(reg)
                st.warning(f"Salida de {total_s} Ton")
            else:
                st.error("Stock insuficiente")

# --- SECCIÓN DE TOTALES (ACUMULADOS) ---
st.divider()
try:
    df_full = conn.read(spreadsheet=URL_DE_TU_HOJA)
    # Calculamos totales filtrando por la columna 'Tipo'
    total_ingresado = df_full[df_full['Tipo'] == 'INGRESO']['Movimiento'].sum()
    total_sacado = abs(df_full[df_full['Tipo'] == 'SALIDA']['Movimiento'].sum())
    stock_actual_calc = total_ingresado - total_sacado

    st.subheader("📊 Resumen de Movimientos Totales")
    m1, m2, m3 = st.columns(3)
    m1.metric("TOTAL INGRESADO", f"{total_ingresado:,.2f} Ton", delta_color="normal")
    m2.metric("TOTAL SACADO (OCUPADO)", f"{total_sacado:,.2f} Ton", delta_color="inverse")
    m3.metric("STOCK REAL EN BODEGA", f"{stock_actual_calc:,.2f} Ton")
except:
    st.info("Cargando resumen desde Google Sheets...")

# --- VISUALIZACIÓN POR LOSAS ---
st.divider()
st.write("### 🏗️ Detalle por Ubicación")
for i in range(0, 7, 4):
    cols = st.columns(4)
    for j in range(4):
        idx = i + j
        if idx < 7:
            with cols[j]:
                nombre = f"Losa {idx+1}"
                st.write(f"**{nombre}**")
                st.table(pd.DataFrame.from_dict(st.session_state.inventario[nombre], orient='index', columns=['Ton']))

# --- HISTORIAL ---
st.subheader("📜 Últimos Movimientos")
try:
    st.dataframe(df_full.tail(15), use_container_width=True)
except:
    pass
