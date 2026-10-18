import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import urllib.parse

# Configuración de página
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

# 1. PERSISTENCIA: Mantener participantes y gastos guardados en la sesión
if 'participantes' not in st.session_state:
    st.session_state.participantes = ["Participante 1", "Participante 2"]

if 'gastos' not in st.session_state:
    st.session_state.gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])

# Pestañas principales
tab1, tab2, tab3 = st.tabs(["📊 Resumen & WhatsApp", "💸 Registrar Gasto", "👥 Participantes"])

# --- PESTAÑA 3: PARTICIPANTES ---
with tab3:
    st.subheader("Configuración de Participantes")
    nuevo_p = st.text_input("Nombre del nuevo participante")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Agregar Participante"):
            if nuevo_p and nuevo_p not in st.session_state.participantes:
                st.session_state.participantes.append(nuevo_p)
                st.success(f"Se agregó a {nuevo_p}")
                st.rerun()
            elif nuevo_p in st.session_state.participantes:
                st.warning("El participante ya existe.")
    
    with col2:
        if st.button("Reiniciar Lista"):
            st.session_state.participantes = ["Participante 1", "Participante 2"]
            st.rerun()
            
    st.markdown("---")
    st.write("**Lista de Participantes:**")
    for p in st.session_state.participantes:
        st.write(f"- {p}")

# --- PESTAÑA 2: REGISTRAR GASTO ---
with tab2:
    st.subheader("Registrar Nuevo Gasto")
    
    if len(st.session_state.participantes) == 0:
        st.warning("Por favor agregue al menos un participante.")
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
        # Mostrar tabla limpia sin columnas de tipo ni emojis
        st.dataframe(st.session_state.gastos, use_container_width=True)
        
        total_acumulado = st.session_state.gastos["Monto"].sum()
        st.metric("Total Acumulado", f"${total_acumulado:,.2f}")
        
        if st.button("Eliminar Último Gasto"):
            st.session_state.gastos = st.session_state.gastos.iloc[:-1].reset_index(drop=True)
            st.rerun()
            
        st.markdown("---")
        st.subheader("Enviar Detalle por WhatsApp")
        
        # 2. FORMATO FORMAL: Sin emojis ni tipos de clasificación
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
