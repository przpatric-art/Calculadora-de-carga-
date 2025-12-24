import streamlit as st
import pandas as pd
from datetime import datetime
import io

# 1. CONFIGURACIÓN VISUAL Y TEMA
st.set_page_config(
    page_title="Control de Carga Industrial v2", 
    page_icon="⚒️", 
    layout="wide"
)

# Estilo CSS para una interfaz limpia y profesional
st.markdown("""
    <style>
    .stButton>button { border-radius: 10px; height: 3.5em; font-weight: bold; }
    .stMetric { background-color: #f1f3f5; padding: 15px; border-radius: 10px; border-bottom: 4px solid #343a40; }
    [data-testid="stExpander"] { border: 1px solid #dee2e6; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN ---
if 'inventario' not in st.session_state:
    st.session_state.inventario = {
        f"Losa {i+1}": {f"Lote {j+1}": 0.0 for j in range(6)} for i in range(7)
    }
if 'historial' not in st.session_state:
    st.session_state.historial = []

# --- FUNCIÓN PROCESAR EXCEL (RESTAURACIÓN) ---
def procesar_excel_subido(file):
    try:
        # Intentamos leer la hoja de 'Stock Final' si existe, si no, la primera disponible
        dict_excel = pd.read_excel(file, sheet_name=None)
        
        # Prioridad 1: Restaurar desde la hoja de Stock Final (si existe)
        if 'Stock Final' in dict_excel:
            df_stock = dict_excel['Stock Final']
            nuevo_inv = {f"Losa {i+1}": {f"Lote {j+1}": 0.0 for j in range(6)} for i in range(7)}
            for _, fila in df_stock.iterrows():
                losa, lote, cant = str(fila['Losa']), str(fila['Lote']), float(fila['Toneladas'])
                if losa in nuevo_inv and lote in nuevo_inv[losa]:
                    nuevo_inv[losa][lote] = cant
            st.session_state.inventario = nuevo_inv
        
        # Prioridad 2: Cargar el historial
        if 'Historial' in dict_excel:
            st.session_state.historial = dict_excel['Historial'].to_dict('records')
        
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("🛠️ Panel de Control")
    st.write("Carga el reporte anterior para continuar:")
    archivo = st.file_uploader("Subir Reporte .xlsx", type=["xlsx"])
    if archivo and st.button("🔄 Sincronizar Sistema", use_container_width=True):
        if procesar_excel_subido(archivo):
            st.success("Sincronizado")
            st.rerun()
    st.divider()
    if st.checkbox("Habilitar Reinicio"):
        if st.button("⚠️ BORRAR TODO (CERO)"):
            st.session_state.clear()
            st.rerun()

# --- HEADER ---
st.title("🌐Control de Carga y Stock Industrial")
st.caption(f"Registro de actividad: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

total_g = sum(sum(l.values()) for l in st.session_state.inventario.values())
m1, m2, m3 = st.columns(3)
m1.metric("📦 STOCK GLOBAL", f"{total_g:,.1f} Ton")
m2.metric("🚛 MOVIMIENTOS", len(st.session_state.historial))
m3.metric("🚦 ESTADO", "Operativo")

st.divider()

# --- OPERACIONES ---
col_in, col_out = st.columns(2)

with col_in:
    with st.expander("📥 REGISTRO DE ENTRADA", expanded=True):
        l_in = st.selectbox("Losa Destino", [f"Losa {i+1}" for i in range(7)], key="in1")
        lt_in = st.selectbox("Lote Destino", [f"Lote {j+1}" for j in range(6)], key="in2")
        t_in = st.number_input("Tonelaje Ingreso", min_value=0.0, step=10.0)
        if st.button("✅ Confirmar Ingreso", type="primary", use_container_width=True):
            st.session_state.inventario[l_in][lt_in] += t_in
            reg = {"Fecha": datetime.now().strftime("%d/%m/%Y"), "Hora": datetime.now().strftime("%H:%M:%S"),
                   "Tipo": "INGRESO", "Ubicación": f"{l_in} - {lt_in}", "Movimiento": f"+{t_in}",
                   "Stock Final Lote": st.session_state.inventario[l_in][lt_in]}
            st.session_state.historial.insert(0, reg)
            st.toast(f'Ingreso en {l_in}', icon='📥')

with col_out:
    with st.expander("📤 REGISTRO DE SALIDA", expanded=True):
        l_out = st.selectbox("Losa Origen", [f"Losa {i+1}" for i in range(7)], key="out1")
        lt_out = st.selectbox("Lote Origen", [f"Lote {j+1}" for j in range(6)], key="out2")
        balde = st.number_input("Peso Balde", value=3.5, step=0.1)
        cant_p = st.number_input("Cantidad Paladas", min_value=0, step=1)
        total_d = round(balde * cant_p, 2)
        st.markdown(f"**Total Despacho:** `{total_d} Ton`")
        if st.button("➖ Confirmar Despacho", use_container_width=True):
            if st.session_state.inventario[l_out][lt_out] >= total_d:
                st.session_state.inventario[l_out][lt_out] -= total_d
                reg = {"Fecha": datetime.now().strftime("%d/%m/%Y"), "Hora": datetime.now().strftime("%H:%M:%S"),
                       "Tipo": "SALIDA", "Ubicación": f"{l_out} - {lt_out}", "Movimiento": f"-{total_d}",
                       "Stock Final Lote": st.session_state.inventario[l_out][lt_out]}
                st.session_state.historial.insert(0, reg)
                st.toast(f'Despacho desde {l_out}', icon='📤')
            else:
                st.error("🚨 Stock Insuficiente")

st.divider()

# --- MONITOR DE SEMÁFORO (ESCALA 20 - 700) ---
st.subheader("📊 Monitor de Inventario (Semáforo Industrial)")
st.info("🔴 Lleno (>700 Ton) | 🟡 Medio (20-700 Ton) | 🟢 Vacío-Bajo (<20 Ton)")

for i in range(0, 7, 4):
    cols = st.columns(4)
    for j in range(4):
        idx = i + j
        if idx < 7:
            with cols[j]:
                nombre = f"Losa {idx+1}"
                st.markdown(f"**{nombre}**")
                tabla = []
                for lote, stock in st.session_state.inventario[nombre].items():
                    sem = "🔴" if stock > 700 else "🟡" if stock >= 20 else "🟢"
                    tabla.append({"E": sem, "Lote": lote, "Stock": f"{stock:,.1f}"})
                st.table(pd.DataFrame(tabla))

# --- GENERACIÓN DE REPORTE INTEGRAL ---
if st.session_state.historial:
    st.divider()
    st.subheader("💾 Cierre de Turno")
    
    # 1. Preparar datos de Stock Final para la segunda hoja
    datos_stock_final = []
    for losa, lotes in st.session_state.inventario.items():
        for lote, ton in lotes.items():
            datos_stock_final.append({"Losa": losa, "Lote": lote, "Toneladas": ton})
    df_stock_final = pd.DataFrame(datos_stock_final)
    df_historial = pd.DataFrame(st.session_state.historial)

    # 2. Crear Excel con dos hojas
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_historial.to_excel(writer, index=False, sheet_name='Historial')
        df_stock_final.to_excel(writer, index=False, sheet_name='Stock Final')
    
    st.download_button(
        label="📥 DESCARGAR REPORTE Y BALANCE FINAL (Excel)",
        data=output.getvalue(),
        file_name=f"Balance_Carga_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
