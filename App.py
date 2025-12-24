import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Control de Carga a Granel", page_icon="⚒️")

st.title("⚒️Distribución de Carga a Granel")
st.write("Gestiona el inventario basado en las paladas del cargador frontal.")

# --- SECCIÓN DE ENTRADA DE DATOS ---
st.sidebar.header("Configuración Inicial")
material = st.sidebar.selectbox("Tipo de Material", ["Arena", "Sal", "Gravilla", "Tierra", "Otro"])
total_existente = st.sidebar.number_input("Cantidad Total en Almacén (Toneladas)", min_value=0.0, value=100.0, step=1.0)
capacidad_balde = st.sidebar.number_input("Capacidad del Balde (Toneladas por palada)", min_value=0.1, value=3.5, step=0.1)

st.divider()

# --- CÁLCULOS ---
st.subheader(f"Registro de Carga: {material}")
paladas_usadas = st.number_input("Número de paladas realizadas", min_value=0, value=0, step=1)

cantidad_ocupada = paladas_usadas * capacidad_balde
cantidad_restante = total_existente - cantidad_ocupada

# --- RESULTADOS ---
col1, col2 = st.columns(2)

with col1:
    st.metric(label="Producto Ocupado", value=f"{cantidad_ocupada:.2f} Ton")

with col2:
    # Color de alerta si nos quedamos sin material
    color = "normal" if cantidad_restante > 0 else "inverse"
    st.metric(label="Saldo en Almacén", value=f"{cantidad_restante:.2f} Ton", delta_color=color)

# Barra de progreso visual
porcentaje_restante = max(0.0, cantidad_restante / total_existente)
st.write(f"**Estado del inventario ({int(porcentaje_restante * 100)}%)**")
st.progress(porcentaje_restante)

if cantidad_restante < 0:
    st.error("⚠️ ¡Cuidado! Las paladas exceden la cantidad total disponible en el almacén.")
