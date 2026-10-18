import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import urllib.parse
import json
import os

st.set_page_config(page_title="Divisor de Gastos & WhatsApp", page_icon="💸", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("Divisor de Gastos & WhatsApp")
st.markdown("---")

DATA_FILE = "gastos_data.json"

def cargar_datos():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                participantes = data.get("participantes", ["Participante 1", "Participante 2"])
                gastos_dict = data.get("gastos", [])
                gastos = pd.DataFrame(gastos_dict)
                if gastos.empty:
                    gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])
                return participantes, gastos
        except:
            pass
    return ["Participante 1", "Participante 2"], pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])

def guardar_datos(participantes, gastos):
    data = {
        "participantes": participantes,
        "gastos": gastos.to_dict(orient="records")
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'participantes' not in st.session_state or 'gastos' not in st.session_state:
    p, g = cargar_datos()
    st.session_state.participantes = p
    st.session_state.gastos = g

pestanas = st.tabs(["📊 Resumen & WhatsApp", "💸 Registrar Gasto", "👥 Participantes"])

# Pestaña de Participantes
with pestanas[2]:
    st.subheader("Configuración de Participantes")
    nuevo_participante = st.text_input("Nombre del nuevo participante")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Agregar participante"):
            if nuevo_participante and nuevo_participante not in st.session_state.participantes:
                st.session_state.participantes.append(nuevo_participante)
                guardar_datos(st.session_state.participantes, st.session_state.gastos)
                st.success(f"Se agregó a {nuevo_participante}")
                st.rerun()
            elif nuevo_participante in st.session_state.participantes:
                st.warning("Ese participante ya existe.")
    with col2:
        if st.button("Reiniciar lista"):
            st.session_state.participantes = ["Participante 1", "Participante 2"]
            guardar_datos(st.session_state.participantes, st.session_state.gastos)
            st.rerun()

    st.write("**Participantes actuales:**")
    for p in st.session_state.participantes:
        st.write(f"- {p}")

# Pestaña de Registrar Gasto
with pestanas[1]:
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
                    guardar_datos(st.session_state.participantes, st.session_state.gastos)
                    st.success("Gasto registrado exitosamente.")
                else:
                    st.error("Por favor complete todos los campos y seleccione participantes.")

# Pestaña de Resumen & WhatsApp
with pestanas[0]:
    st.subheader("Resumen de Cuentas")
    if len(st.session_state.gastos) > 0:
        st.write("**Detalle de Compras:**")
        st.dataframe(st.session_state.gastos, use_container_width=True)
        
        total_general = st.session_state.gastos["Monto"].sum()
        st.metric("Gasto Total Acumulado", f"${total_general:,.2f}")
        
        saldos = {p: 0.0 for p in st.session_state.participantes}
        for _, row in st.session_state.gastos.iterrows():
            pagador = row["Pagado por"]
            monto = row["Monto"]
            beneficiarios = [p.strip() for p in row["Participantes"].split(",") if p.strip() in saldos]
            if beneficiarios:
                cuota = monto / len(beneficiarios)
                if pagador in saldos:
                    saldos[pagador] += monto
                for b in beneficiarios:
                    saldos[b] -= cuota

        st.markdown("---")
        st.write("**Estado de Cuentas por Persona:**")
        resumen_cuentas_txt = []
        for p, saldo in saldos.items():
            if saldo > 0.01:
                txt = f"{p}: debe recibir ${saldo:,.2f}"
                st.write(f"- {txt}")
                resumen_cuentas_txt.append(txt)
            elif saldo < -0.01:
                txt = f"{p}: debe pagar ${abs(saldo):,.2f}"
                st.write(f"- {txt}")
                resumen_cuentas_txt.append(txt)
            else:
                txt = f"{p}: al día ($0.00)"
                st.write(f"- {txt}")
                resumen_cuentas_txt.append(txt)
                
        if st.button("Eliminar último gasto"):
            st.session_state.gastos = st.session_state.gastos.iloc[:-1].reset_index(drop=True)
            guardar_datos(st.session_state.participantes, st.session_state.gastos)
            st.rerun()
            
        st.markdown("---")
        st.subheader("Enviar Detalle por WhatsApp")
        
        lineas = []
        lineas.append("RESUMEN DE GASTOS COMPARTIDOS")
        lineas.append("")
        lineas.append("DETALLE DE COMPRAS:")
        lineas.append("")
        
        for index, row in st.session_state.gastos.iterrows():
            num = index + 1
            lineas.append(f"Gasto {num}:")
            lineas.append(f"- Fecha: {row['Fecha']}")
            lineas.append(f"- Descripción: {row['Descripción']}")
            lineas.append(f"- Pagado por: {row['Pagado por']}")
            lineas.append(f"- Monto: ${row['Monto']:,.2f}")
            lineas.append(f"- Dividido entre: {row['Participantes']}")
            lineas.append("")
            lineas.append("")
            
        lineas.append("----------------------------------")
        lineas.append("")
        lineas.append(f"TOTAL GENERAL: ${total_general:,.2f}")
        lineas.append("")
        lineas.append("ESTADO DE CUENTAS:")
        for r in resumen_cuentas_txt:
            lineas.append(f"- {r}")
            
        mensaje = "\n".join(lineas)
        
        url_whatsapp = f"https://api.whatsapp.com/send?text={urllib.parse.quote(mensaje)}"
        st.markdown(f'<a href="{url_whatsapp}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer; width:100%;">Enviar por WhatsApp</button></a>', unsafe_allow_html=True)
    else:
        st.info("Aún no hay gastos registrados.")
