import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import urllib.parse

# Configuración de página
st.set_page_config(page_title="Divisor de Gastos", page_icon="💸", layout="centered")

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("Divisor de Gastos")
st.markdown("---")

# 1. MANTENER PARTICIPANTES Y GASTOS EN MEMORIA (no se borran al navegar)
if 'participantes' not in st.session_state:
    st.session_state.participantes = ["Persona 1", "Persona 2", "Persona 3"]

if 'gastos' not in st.session_state:
    st.session_state.gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])

# Pestañas principales de la aplicación
tab_registro, tab_resumen, tab_participantes = st.tabs([
    "Registrar Gasto", 
    "Resumen & WhatsApp", 
    "Participantes"
])

# --- PESTAÑA: PARTICIPANTES ---
with tab_participantes:
    st.subheader("Gestión de Participantes")
    
    nuevo_p = st.text_input("Agregar nuevo participante:", placeholder="Nombre...")
    col_add, col_reset = st.columns(2)
    
    with col_add:
        if st.button("Agregar"):
            if nuevo_p and nuevo_p not in st.session_state.participantes:
                st.session_state.participantes.append(nuevo_p)
                st.success(f"{nuevo_p} fue agregado a la lista.")
                st.rerun()
            elif nuevo_p in st.session_state.participantes:
                st.warning("Ese nombre ya está en la lista.")
                
    with col_reset:
        if st.button("Restablecer Lista"):
            st.session_state.participantes = ["Persona 1", "Persona 2", "Persona 3"]
            st.rerun()

    st.write("---")
    st.write("**Lista actual de participantes:**")
    for p in st.session_state.participantes:
        st.write(f"• {p}")

# --- PESTAÑA: REGISTRAR GASTO ---
with tab_registro:
    st.subheader("Registrar Nuevo Gasto")
    
    if len(st.session_state.participantes) == 0:
        st.warning("Debe agregar al menos un participante para registrar gastos.")
    else:
        with st.form("form_nuevo_gasto", clear_on_submit=True):
            descripcion = st.text_input("Descripción del gasto", placeholder="Ej. Cena, Supermercado...")
            monto = st.number_input("Monto total ($)", min_value=0.0, step=100.0, format="%.2f")
            pagador = st.selectbox("Pagado por", st.session_state.participantes)
            dividir_entre = st.multiselect("Dividir entre", st.session_state.participantes, default=st.session_state.participantes)
            fecha = st.date_input("Fecha del gasto", datetime.now())
            
            guardar = st.form_submit_button("Guardar Gasto")
            
            if guardar:
                if descripcion and monto > 0 and dividir_entre:
                    nuevo_registro = pd.DataFrame({
                        "Fecha": [fecha.strftime("%d/%m/%Y")],
                        "Descripción": [descripcion],
                        "Pagado por": [pagador],
                        "Monto": [monto],
                        "Participantes": [", ".join(dividir_entre)]
                    })
                    st.session_state.gastos = pd.concat([st.session_state.gastos, nuevo_registro], ignore_index=True)
                    st.success("Gasto registrado correctamente.")
                else:
                    st.error("Por favor complete la descripción, el monto y al menos un participante.")

# --- PESTAÑA: RESUMEN & WHATSAPP ---
with tab_resumen:
    st.subheader("Resumen General y Balance")
    
    if len(st.session_state.gastos) > 0:
        # Muestra la tabla de gastos formal (sin columnas de tipo ni emojis)
        st.write("**Historial de Gastos Registrados:**")
        st.dataframe(st.session_state.gastos, use_container_width=True)
        
        monto_total = st.session_state
