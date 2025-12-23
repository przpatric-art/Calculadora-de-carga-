import streamlit as st

st.title("🧮 Mi Calculadora de Préstamos")
st.write("Introduce los datos para calcular tu cuota mensual.")

# Entradas de usuario
monto = st.number_input("Monto del préstamo ($)", min_value=0.0, value=1000.0)
interes = st.slider("Interés anual (%)", 0.0, 50.0, 5.0)
plazo = st.number_input("Plazo (meses)", min_value=1, value=12)

# Lógica del cálculo
tasa_mensual = (interes / 100) / 12
if tasa_mensual > 0:
    cuota = (monto * tasa_mensual) / (1 - (1 + tasa_mensual)**-plazo)
else:
    cuota = monto / plazo

# Resultado
st.subheader(f"Tu cuota mensual es: ${cuota:,.2f}")
