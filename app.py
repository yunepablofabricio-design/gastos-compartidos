import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import urllib.parse

# Configuración de la página
st.set_page_config(page_title="Divisor de Gastos & WhatsApp", page_icon="💸", layout="centered")

# Estilos CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("Divisor de Gastos & WhatsApp")
st.markdown("---")

# Inicialización del estado (comienza vacío si no hay participantes guardados)
if 'participantes' not in st.session_state:
    st.session_state.participantes = []

if 'gastos' not in st.session_state:
    st.session_state.gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])

# Pestañas principales
tab1, tab2, tab3 = st.tabs(["📊 Resumen & WhatsApp", "💸 Registrar Gasto", "👥 Participantes"])

# --- PESTAÑA 3: PARTICIPANTES ---
with tab3:
    st.subheader("Configuración de Participantes")
    
    nuevo_p = st.text_input("Nombre del participante")
    
    col_add, col_clear = st.columns(2)
    with col_add:
        if st.button("Agregar Participante"):
            if nuevo_p and nuevo_p.strip() not in st.session_state.participantes:
                st.session_state.participantes.append(nuevo_p.strip())
                st.success(f"Se agregó a {nuevo_p.strip()}")
                st.rerun()
            elif nuevo_p.strip() in st.session_state.participantes:
                st.warning("El participante ya está en la lista.")
    
    with col_clear:
        if st.button("Vaciar Lista"):
            st.session_state.participantes = []
            st.rerun()
            
    st.markdown("---")
    st.write("**Lista Actual de Participantes:**")
    
    if len(st.session_state.participantes) == 0:
        st.info("No hay participantes registrados. Agrega uno arriba.")
    else:
        # Permitir eliminar participantes individualmente
        for i, p in enumerate(st.session_state.participantes):
            col_nombre, col_borrar = st.columns([3, 1])
            with col_nombre:
                st.write(f"• {p}")
            with col_borrar:
                if st.button("Eliminar", key=f"del_{i}"):
                    st.session_state.participantes.pop(i)
                    st.rerun()

# --- PESTAÑA 2: REGISTRAR GASTO ---
with tab2:
    st.subheader("Registrar Nuevo Gasto")
    
    if len(st.session_state.participantes) == 0:
        st.warning("Por favor agrega al menos un participante en la pestaña '👥 Participantes'.")
    else:
        with st.form("form_gasto", clear_on_submit=True):
            descripcion = st.text_input("Descripción del gasto")
            monto = st.number_input("Monto total ($)", min_value=0.0, format="%.2f")
            pagador = st.selectbox("Pagado por", st.session_state.participantes)
            dividir_entre = st.multiselect("Dividir entre", st.session_state.participantes, default=st.session_state.participantes)
            fecha = st.date_input("Fecha", datetime.now())
            
            submit = st.form_submit_button("Guardar Gasto")
            
            if submit:
                if descripcion and monto > 0 and dividir_entre:
                    nuevo_gasto = pd.DataFrame({
                        "Fecha": [fecha.strftime("%d/%m/%Y")],
                        "Descripción": [descripcion],
                        "Pagado por": [pagador],
                        "Monto": [monto],
                        "Participantes": [", ".join(dividir_entre)]
                    })
                    st.session_state.gastos = pd.concat([st.session_state.gastos, nuevo_gasto], ignore_index=True)
                    st.success("Gasto guardado con éxito.")
                else:
                    st.error("Por favor complete la descripción, el monto y al menos un participante.")

# --- PESTAÑA 1: RESUMEN & WHATSAPP ---
with tab1:
    st.subheader("Resumen General de Cuentas")
    
    if len(st.session_state.gastos) > 0:
        st.write("**Historial de Gastos:**")
        st.dataframe(st.session_state.gastos, use_container_width=True)
        
        total_acumulado = st.session_state.gastos["Monto"].sum()
        st.metric("Total Acumulado", f"${total_acumulado:,.2f}")
        
        if st.button("Eliminar Último Gasto"):
            st.session_state.gastos = st.session_state.gastos.iloc[:-1].reset_index(drop=True)
            st.rerun()
            
        st.markdown("---")
        st.subheader("Enviar Detalle por WhatsApp")
        
        # Mensaje formal para WhatsApp sin emojis ni clasificaciones de tipo
        mensaje = "RESUMEN DE GASTOS COMPARTIDOS\n\n"
        for idx, row in st.session_state.gastos.iterrows():
            mensaje += f"- Fecha: {row['Fecha']}\n"
            mensaje += f"  Descripción: {row['Descripción']}\n"
            mensaje += f"  Pagado por: {row['Pagado por']}\n"
            mensaje += f"  Monto: ${row['Monto']:,.2f}\n"
            mensaje += f"  Dividido entre: {row['Participantes']}\n\n"
            
        mensaje += f"Total General: ${total_acumulado:,.2f}"
        
        url_whatsapp = f"https://api.whatsapp.com/send?text={urllib.parse.quote(mensaje)}"
        st.markdown(f'<a href="{url_whatsapp}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:12px 20px; border-radius:6px; font-weight:bold; cursor:pointer; width:100%;">Enviar por WhatsApp</button></a>', unsafe_allow_html=True)
    else:
        st.info("Aún no hay gastos registrados.")
