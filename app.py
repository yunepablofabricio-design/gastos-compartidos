import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import urllib.parse

st.set_page_config(page_title="Gestión de Gastos Compartidos", page_icon="💰", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("Gestión de Gastos Compartidos")
st.markdown("---")

if 'participantes' not in st.session_state:
    st.session_state.participantes = ["Participante 1", "Participante 2"]

if 'gastos' not in st.session_state:
    st.session_state.gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])

pestanas = st.tabs(["Registrar Gasto", "Participantes", "Resumen & WhatsApp"])

with pestanas[1]:
    st.subheader("Configuración de Participantes")
    nuevo_participante = st.text_input("Nombre del nuevo participante")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Agregar participante"):
            if nuevo_participante and nuevo_participante not in st.session_state.participantes:
                st.session_state.participantes.append(nuevo_participante)
                st.success(f"Se agregó a {nuevo_participante}")
                st.rerun()
            elif nuevo_participante in st.session_state.participantes:
                st.warning("Ese participante ya existe.")
    with col2:
        if st.button("Reiniciar lista"):
            st.session_state.participantes = ["Participante 1", "Participante 2"]
            st.rerun()

    st.write("**Participantes actuales:**")
    for i, p in enumerate(st.session_state.participantes):
        st.write(f"- {p}")

with pestanas[0]:
    st.subheader("Registrar Nuevo Gasto")
    if len(st.session_state.participantes) == 0:
        st.warning("Por favor, agregue al menos un participante en la pestaña 'Participantes'.")
    else:
        with st.form("form_gasto"):
            descripcion = st.text_input("Descripción del gasto")
            monto = st.number_input("Monto total", min_value=0.0, format="%.2f")
            pagador = st.selectbox("Pagado por", st.session_state.participantes)
            dividir_entre = st.multiselect("Dividir entre", st.session_state.participantes, default=st.session_state.participantes)
            fecha = st.date_input("Fecha", datetime.now())
            
            submit = st.form_submit_button("Guardar Gasto")
            if submit:
                if descripcion and monto > 0 and dividir_entre:
                    nuevo_gasto = pd.DataFrame({
                        "Fecha": [fecha.strftime("%Y-%m-%d")],
                        "Descripción": [descripcion],
                        "Pagado por": [pagador],
                        "Monto": [monto],
                        "Participantes": [", ".join(dividir_entre)]
                    })
                    st.session_state.gastos = pd.concat([st.session_state.gastos, nuevo_gasto], ignore_index=True)
                    st.success("Gasto registrado exitosamente.")
                else:
                    st.error("Por favor complete todos los campos y seleccione participantes.")

with pestanas[2]:
    st.subheader("Resumen de Cuentas")
    if len(st.session_state.gastos) > 0:
        st.write("**Detalle de Gastos:**")
        st.dataframe(st.session_state.gastos, use_container_width=True)
        
        total_general = st.session_state.gastos["Monto"].sum()
        st.metric("Gasto Total Acumulado", f"${total_general:,.2f}")
        
        if st.button("Eliminar último gasto"):
            st.session_state.gastos = st.session_state.gastos.iloc[:-1].reset_index(drop=True)
            st.rerun()
            
        st.markdown("---")
        st.subheader("Enviar Detalle por WhatsApp")
        
        mensaje = "RESUMEN DE GASTOS COMPARTIDOS\n\n"
        for index, row in st.session_state.gastos.iterrows():
            mensaje += f"- Fecha: {row['Fecha']}\n"
            mensaje += f"  Descripción: {row['Descripción']}\n"
            mensaje += f"  Pagado por: {row['Pagado por']}\n"
            mensaje += f"  Monto: ${row['Monto']:,.2f}\n"
            mensaje += f"  Dividido entre: {row['Participantes']}\n\n"
        mensaje += f"Total General: ${total_general:,.2f}"
        
        url_whatsapp = f"https://api.whatsapp.com/send?text={urllib.parse.quote(mensaje)}"
        st.markdown(f'<a href="{url_whatsapp}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer; width:100%;">Enviar por WhatsApp</button></a>', unsafe_allow_html=True)
    else:
        st.info("Aún no hay gastos registrados.")
