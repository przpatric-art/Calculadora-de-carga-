import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Control de Carga Pro", layout="wide")

# --- INICIALIZACIÓN DE MEMORIA ---
if 'inventario' not in st.session_state:
    st.session_state.inventario = {
        f"Losa {i+1}": {f"Lote {j+1}": 0.0 for j in range(6)} for i in range(7)
    }
if 'historial' not in st.session_state:
    st.session_state.historial = []

# --- FUNCIÓN PARA PROCESAR EL ARCHIVO SUBIDO ---
def procesar_archivo_subido(file):
    try:
        # Leer el CSV con codificación compatible
        df = pd.read_csv(file, encoding='utf-8-sig')
        
        if 'Ubicación' in df.columns and 'Stock Final Lote' in df.columns:
            # 1. Limpiar el inventario actual antes de cargar
            nuevo_inv = {f"Losa {i+1}": {f"Lote {j+1}": 0.0 for j in range(6)} for i in range(7)}
            
            # 2. Reconstruir el stock basándose en el último registro de cada ubicación en el CSV
            # Invertimos el DF para encontrar el valor más reciente primero
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
            
            # 3. Actualizar session_state
            st.session_state.inventario = nuevo_inv
            st.session_state.historial = df.to_dict('records')
            return True
        else:
            st.error("⚠️ El archivo no tiene el formato correcto de columnas.")
            return False
    except Exception as e:
        st.error(f"❌ Error técnico al procesar: {e}")
        return False

# --- BARRA LATERAL (RESTAURACIÓN) ---
with st.sidebar:
    st.header("📂 Restaurar Datos")
    st.info("Sube el reporte .csv descargado anteriormente para recuperar el stock.")
    
    archivo = st.file_uploader("Seleccionar archivo CSV", type=["csv"], key="cargador_csv")
    
    if archivo is not None:
        if st.button("🔄 Aplicar y Cargar Inventario", use_container_width=True):
            if procesar_archivo_subido(archivo):
                st.success("✅ ¡Datos restaurados!")
                st.rerun()

# --- PANEL PRINCIPAL ---
st.title(f"⚒️Control de Carga  {datetime.now().strftime('%d/%m/%Y')}")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("📥 Registro de Ingreso")
        l_in = st.selectbox("Losa", [f"Losa {i+1}" for i in range(7)], key="l_in")
        lt_in = st.selectbox("Lote", [f"Lote {j+1}" for j in range(6)], key="lt_in")
        cant_in = st.number_input("Toneladas que ingresan", min_value=0.0, step=0.1, key="c_in")
        
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
            st.success(f"Sumado a {l_in}")

with col2:
    with st.container(border=True):
        st.subheader("📤 Registro de Salida")
        l_out = st.selectbox("Losa", [f"Losa {i+1}" for i in range(7)], key="l_out")
        lt_out = st.selectbox("Lote", [f"Lote {j+1}" for j in range(6)], key="lt_out")
        p_balde = st.number_input("Peso Balde (Ton)", value=3.5)
        n_paladas = st.number_input("Cantidad de Paladas", min_value=0, step=1)
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
                st.error("⚠️ Stock insuficiente en el lote seleccionado.")

# --- MONITOR DE STOCK ---
st.divider()
total_g = sum(sum(l.values()) for l in st.session_state.inventario.values())
st.metric("📦 STOCK TOTAL GLOBAL", f"{total_g:,.2f} Ton")

# Mostrar las 7 losas en columnas
for i in range(0, 7, 4):
    cols = st.columns(4)
    for j in range(4):
        idx = i + j
        if idx < 7:
            with cols[j]:
                nombre = f"Losa {idx+1}"
                st.write(f"**{nombre}**")
                df_losa = pd.DataFrame.from_dict(st.session_state.inventario[nombre], orient='index', columns=['Ton'])
                st.dataframe(df_losa, use_container_width=True)

# --- REPORTE Y DESCARGA ---
st.divider()
if st.session_state.historial:
    st.subheader("📜 Historial Acumulado")
    df_h = pd.DataFrame(st.session_state.historial)
    st.dataframe(df_h, use_container_width=True)
    
    nombre_archivo = f"Control_Carga_{datetime.now().strftime('%d_%m_%Y')}.csv"
    csv = df_h.to_csv(index=False).encode('utf-8-sig')
    
    st.download_button(
        label=f"📥 Descargar Reporte: {nombre_archivo}",
        data=csv,
        file_name=nombre_archivo,
        mime='text/csv',
        use_container_width=True
    )
