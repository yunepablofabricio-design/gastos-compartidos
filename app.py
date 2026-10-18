import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import urllib.parse

# Configuración de página
st.set_page_config(page_title="Divisor de Gastos & WhatsApp", page_icon="💸", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("Divisor de Gastos & WhatsApp")
st.markdown("---")

# Inicialización de estado para persistencia
if 'participantes' not in st.session_state:
    st.session_state.participantes = []

if 'gastos' not in st.session_state:
    st.session_state.gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])

# Pestañas principales
tab_resumen, tab_registro, tab_participantes = st.tabs([
    "📊 Resumen & WhatsApp", 
    "💸 Registrar Gasto", 
    "👥 Participantes"
])

# --- PESTAÑA: PARTICIPANTES ---
with tab_participantes:
    st.subheader("Configuración de Participantes")
    nuevo_p = st.text_input("Nombre del nuevo participante")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Agregar Participante"):
            if nuevo_p and nuevo_p.strip() not in st.session_state.participantes:
                st.session_state.participantes.append(nuevo_p.strip())
                st.success(f"Se agregó a {nuevo_p.strip()}")
                st.rerun()
            elif nuevo_p.strip() in st.session_state.participantes:
                st.warning("Ese participante ya existe.")
    with col2:
        if st.button("Vaciar Lista"):
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
                st.write(f"- {p}")
            with c2:
                if st.button("Borrar", key=f"del_p_{i}"):
                    st.session_state.participantes.pop(i)
                    st.rerun()

# --- PESTAÑA: REGISTRAR GASTO ---
with tab_registro:
    st.subheader("Registrar Nuevo Gasto")
    
    if len(st.session_state.participantes) == 0:
        st.warning("Por favor, agregue al menos un participante en la pestaña '👥 Participantes'.")
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
                    st.error("Por favor complete todos los campos y seleccione al menos un participante.")

# --- PESTAÑA: RESUMEN & WHATSAPP ---
with tab_resumen:
    st.subheader("Resumen de Cuentas y Detalle por Persona")
    
    if len(st.session_state.gastos) > 0:
        st.write("**Historial de Gastos:**")
        st.dataframe(st.session_state.gastos, use_container_width=True)
        
        total_general = st.session_state.gastos["Monto"].sum()
        st.metric("Gasto Total Acumulado", f"${total_general:,.2f}")
        
        # Calcular cuánto le corresponde a cada uno detalladamente por gasto
        st.markdown("---")
        st.subheader("Detalle de lo que corresponde a cada participante")
        
        # Diccionario para acumular saldos
        balance_individual = {p: 0.0 for p in st.session_state.participantes}
        pagado_individual = {p: 0.0 for p in st.session_state.participantes}
        
        for idx, row in st.session_state.gastos.iterrows():
            monto_gasto = row["Monto"]
            pagador_gasto = row["Pagado por"]
            partic_gasto = [p.strip() for p in row["Participantes"].split(",")]
            
            if pagador_gasto in pagado_individual:
                pagado_individual[pagador_gasto] += monto_gasto
                
            if len(partic_gasto) > 0:
                monto_por_persona = monto_gasto / len(partic_gasto)
                for p in partic_gasto:
                    if p in balance_individual:
                        balance_individual[p] += monto_por_persona

        for p in st.session_state.participantes:
            st.write(f"• **{p}**: Pagó ${pagado_individual.get(p, 0.0):,.2f} | Le corresponde consumir/aportar: ${balance_individual.get(p, 0.0):,.2f}")

        if st.button("Eliminar último gasto"):
            st.session_state.gastos = st.session_state.gastos.iloc[:-1].reset_index(drop=True)
            st.rerun()
            
        st.markdown("---")
        st.subheader("Enviar Detalle por WhatsApp")
        
        # Mensaje formal para WhatsApp (sin emojis ni tipo)
        mensaje = "RESUMEN DE GASTOS COMPARTIDOS\n\n"
        mensaje += "DETALLE DE GASTOS:\n"
        for idx, row in st.session_state.gastos.iterrows():
            mensaje += f"- Fecha: {row['Fecha']}\n"
            mensaje += f"  Descripción: {row['Descripción']}\n"
            mensaje += f"  Pagado por: {row['Pagado por']}\n"
            mensaje += f"  Monto: ${row['Monto']:,.2f}\n"
            mensaje += f"  Dividido entre: {row['Participantes']}\n\n"
            
        mensaje += f"TOTAL GENERAL: ${total_general:,.2f}\n\n"
        mensaje += "BALANCE POR PARTICIPANTE:\n"
        for p in st.session_state.participantes:
            mensaje += f"- {p}: Pagó ${pagado_individual.get(p, 0.0):,.2f} | Le corresponde: ${balance_individual.get(p, 0.0):,.2f}\n"
        
        url_whatsapp = f"https://api.whatsapp.com/send?text={urllib.parse.quote(mensaje)}"
        st.markdown(f'<a href="{url_whatsapp}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:12px 20px; border-radius:6px; font-weight:bold; cursor:pointer; width:100%;">Enviar Resumen por WhatsApp</button></a>', unsafe_allow_html=True)
    else:
        st.info("Aún no hay gastos registrados.")
