import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Configuración de página
st.set_page_config(page_title="Control de Carga Excel", layout="wide")

# --- INICIALIZACIÓN DE MEMORIA ---
if 'inventario' not in st.session_state:
    st.session_state.inventario = {
        f"Losa {i+1}": {f"Lote {j+1}": 0.0 for j in range(6)} for i in range(7)
    }
if 'historial' not in st.session_state:
    st.session_state.historial = []

# --- FUNCIÓN PARA PROCESAR EXCEL ---
def procesar_excel_subido(file):
    try:
        # Leer el archivo Excel
        df = pd.read_excel(file)
        
        if 'Ubicación' in df.columns and 'Stock Final Lote' in df.columns:
            nuevo_inv = {f"Losa {i+1}": {f"Lote {j+1}": 0.0 for j in range(6)} for i in range(7)}
            df_invertido = df.iloc[::-1]
            ubicaciones_procesadas = set()

            for _, fila in df_invertido.iterrows():
                ubi = str(fila['Ubicación'])
                if ubi not in ubicaciones_procesadas:
                    if " - " in ubi:
                        partes = ubi.split(" - ")
                        losa, lote = partes[0], partes[1]
                        if losa in nuevo_inv and lote in nuevo_inv[losa]:
                            nuevo_inv[losa][lote] = float(fila['Stock Final Lote'])
                            ubicaciones_procesadas.add(ubi)
            
            st.session_state.inventario = nuevo_inv
            st.session_state.historial = df.to_dict('records')
            return True
        else:
            st.error("⚠️ El Excel no tiene las columnas 'Ubicación' y 'Stock Final Lote'.")
            return False
    except Exception as e:
        st.error(f"❌ Error al leer Excel: {e}")
        return False

# --- BARRA LATERAL (RESTAURACIÓN) ---
with st.sidebar:
    st.header("📂 Restaurar desde Excel")
    archivo = st.file_uploader("Subir archivo .xlsx", type=["xlsx"])
    
    if archivo is not None:
        if st.button("🔄 Cargar Datos de Excel"):
            if procesar_excel_subido(archivo):
                st.success("✅ ¡Inventario Restaurado!")
                st.rerun()

# --- PANEL PRINCIPAL ---
st.title(f"⚒️ Control de Carga  {datetime.now().strftime('%d/%m/%Y')}")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("📥 Registro de Ingreso")
        l_in = st.selectbox("Losa", [f"Losa {i+1}" for i in range(7)], key="l_in")
        lt_in = st.selectbox("Lote", [f"Lote {j+1}" for j in range(6)], key="lt_in")
        cant_in = st.number_input("Toneladas", min_value=0.0, step=0.1, key="c_in")
        
        if st.button("Confirmar Ingreso", use_container_width=True):
            st.session_state.inventario[l_in][lt_in] += cant_in
            reg = {
                "Fecha": datetime.now().strftime("%d/%m/%Y"),
                "Hora": datetime.now().strftime("%H:%M:%S"),
                "Tipo": "INGRESO",
                "Ubicación": f"{l_in} - {lt_in}",
                "Movimiento": f"+{cant_in}",
                "Stock Final Lote": st.session_state.inventario[l_in][lt_in]
            }
            st.session_state.historial.insert(0, reg)
            st.success("Registrado")

with col2:
    with st.container(border=True):
        st.subheader("📤 Registro de Salida")
        l_out = st.selectbox("Losa", [f"Losa {i+1}" for i in range(7)], key="l_out")
        lt_out = st.selectbox("Lote", [f"Lote {j+1}" for j in range(6)], key="lt_out")
        p_balde = st.number_input("Peso Balde (Ton)", value=3.5)
        n_paladas = st.number_input("Paladas", min_value=0, step=1)
        total_s = round(p_balde * n_paladas, 2)
        
        if st.button("Confirmar Salida", use_container_width=True):
            if st.session_state.inventario[l_out][lt_out] >= total_s:
                st.session_state.inventario[l_out][lt_out] -= total_s
                reg = {
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Hora": datetime.now().strftime("%H:%M:%S"),
                    "Tipo": "SALIDA",
                    "Ubicación": f"{l_out} - {lt_out}",
                    "Movimiento": f"-{total_s}",
                    "Stock Final Lote": st.session_state.inventario[l_out][lt_out]
                }
                st.session_state.historial.insert(0, reg)
                st.warning(f"Salida de {total_s} Ton")
            else:
                st.error("⚠️ Stock insuficiente.")

# --- MONITOR DE STOCK ---
st.divider()
total_g = sum(sum(l.values()) for l in st.session_state.inventario.values())
st.metric("📦 STOCK TOTAL GLOBAL", f"{total_g:,.2f} Ton")

for i in range(0, 7, 4):
    cols = st.columns(4)
    for j in range(4):
        idx = i + j
        if idx < 7:
            with cols[j]:
                nombre = f"Losa {idx+1}"
                st.write(f"**{nombre}**")
                st.dataframe(pd.DataFrame.from_dict(st.session_state.inventario[nombre], orient='index', columns=['Ton']), use_container_width=True)

# --- REPORTE Y DESCARGA EXCEL ---
st.divider()
if st.session_state.historial:
    st.subheader("📜 Historial Acumulado")
    df_h = pd.DataFrame(st.session_state.historial)
    st.dataframe(df_h, use_container_width=True)
    
    # Crear el archivo Excel en memoria para la descarga
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_h.to_excel(writer, index=False, sheet_name='ControlCarga')
    
    nombre_archivo = f"Control_Carga_{datetime.now().strftime('%d_%m_%Y')}.xlsx"
    
    st.download_button(
        label=f"📥 Descargar Excel: {nombre_archivo}",
        data=buffer.getvalue(),
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
