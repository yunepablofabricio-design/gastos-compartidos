import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import urllib.parse

# Configuración de página original con emojis
st.set_page_config(page_title="Divisor de Gastos & WhatsApp", page_icon="💸", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("💸 Divisor de Gastos & WhatsApp")
st.markdown("---")

# Persistencia de datos en la sesión
if 'participantes' not in st.session_state:
    st.session_state.participantes = []

if 'gastos' not in st.session_state:
    st.session_state.gastos = pd.DataFrame(columns=["Fecha", "Tipo", "Descripción", "Pagado por", "Monto", "Participantes"])

if 'alias' not in st.session_state:
    st.session_state.alias = ""

# Pestañas originales con iconos
tab_resumen, tab_registro, tab_participantes = st.tabs([
    "📊 Resumen & WhatsApp", 
    "💸 Registrar Gasto", 
    "👥 Participantes"
])

# --- PESTAÑA: PARTICIPANTES ---
with tab_participantes:
    st.subheader("👥 Configuración de Participantes")
    nuevo_p = st.text_input("Nombre del nuevo participante")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Agregar Participante"):
            if nuevo_p and nuevo_p.strip() not in st.session_state.participantes:
                st.session_state.participantes.append(nuevo_p.strip())
                st.success(f"Se agregó a {nuevo_p.strip()}")
                st.rerun()
            elif nuevo_p.strip() in st.session_state.participantes:
                st.warning("Ese participante ya existe.")
    with col2:
        if st.button("🗑️ Vaciar Lista"):
            st.session_state.participantes = []
            st.rerun()

    st.markdown("---")
    st.write("**Lista Actual de Participantes:**")
    if len(st.session_state.participantes) == 0:
        st.info("No hay participantes registrados. Agrega algunos arriba.")
    else:
        for i, p in enumerate(st.session_state.participantes):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"• {p}")
            with c2:
                if st.button("Borrar", key=f"del_p_{i}"):
                    st.session_state.participantes.pop(i)
                    st.rerun()

# --- PESTAÑA: REGISTRAR GASTO ---
with tab_registro:
    st.subheader("💸 Registrar Nuevo Gasto")
    
    if len(st.session_state.participantes) == 0:
        st.warning("Por favor, agregue al menos un participante en la pestaña '👥 Participantes'.")
    else:
        with st.form("form_gasto", clear_on_submit=True):
            tipo = st.selectbox("Tipo de gasto", ["Comida", "Transporte", "Alojamiento", "Entretenimiento", "Supermercado", "Otros"])
            descripcion = st.text_input("Descripción del gasto")
            monto = st.number_input("Monto total ($)", min_value=0.0, format="%.2f")
            pagador = st.selectbox("Pagado por", st.session_state.participantes)
            dividir_entre = st.multiselect("Dividir entre", st.session_state.participantes, default=st.session_state.participantes)
            fecha = st.date_input("Fecha", datetime.now())
            
            submit = st.form_submit_button("💾 Guardar Gasto")
            if submit:
                if descripcion and monto > 0 and dividir_entre:
                    nuevo_gasto = pd.DataFrame({
                        "Fecha": [fecha.strftime("%d/%m/%Y")],
                        "Tipo": [tipo],
                        "Descripción": [descripcion],
                        "Pagado por": [pagador],
                        "Monto": [monto],
                        "Participantes": [", ".join(dividir_entre)]
                    })
                    st.session_state.gastos = pd.concat([st.session_state.gastos, nuevo_gasto], ignore_index=True)
                    st.success("Gasto guardado con éxito.")
                else:
                    st.error("Por favor complete todos los campos y seleccione al menos un participante.")

# --- PESTAÑA: RESUMEN & WHATSAPP ---
with tab_resumen:
    st.subheader("📊 Resumen de Cuentas y Detalle por Persona")
    
    # Alias / CBU original
    st.session_state.alias = st.text_input("💳 Alias / CBU para recibir transferencias:", value=st.session_state.alias, placeholder="Ejemplo: mi.alias.mp")
    
    if len(st.session_state.gastos) > 0:
        st.write("**📜 Historial Completo de Gastos:**")
        # En la app se sigue mostrando la columna "Tipo"
        st.dataframe(st.session_state.gastos, use
