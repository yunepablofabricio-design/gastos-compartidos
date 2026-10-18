import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import urllib.parse
import json
import os

st.set_page_config(page_title="Gestión de Gastos Compartidos", page_icon="💸", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("Gestión de Gastos Compartidos")
st.markdown("---")

DATA_FILE = "gastos_data.json"

def cargar_datos():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                participantes = data.get("participantes", ["Pablo", "Gerardo", "Emanuel", "Nico"])
                alias_mp = data.get("alias_mp", "pabloyune (Mercado Pago)")
                gastos_dict = data.get("gastos", [])
                gastos = pd.DataFrame(gastos_dict)
                if gastos.empty:
                    gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes", "Personas por Participante"])
                return participantes, alias_mp, gastos
        except:
            pass
    return ["Pablo", "Gerardo", "Emanuel", "Nico"], "pabloyune (Mercado Pago)", pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes", "Personas por Participante"])

def guardar_datos(participantes, alias_mp, gastos):
    data = {
        "participantes": participantes,
        "alias_mp": alias_mp,
        "gastos": gastos.to_dict(orient="records")
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'participantes' not in st.session_state or 'gastos' not in st.session_state:
    p, a, g = cargar_datos()
    st.session_state.participantes = p
    st.session_state.alias_mp = a
    st.session_state.gastos = g

pestanas = st.tabs(["Resumen & WhatsApp", "Registrar Gasto", "Participantes"])

# Pestaña 3: Participantes y Alias
with pestanas[2]:
    st.subheader("Configuración General")
    
    # Configuración de Alias
    nuevo_alias = st.text_input("Alias de Mercado Pago / Cuenta a transferir", value=st.session_state.alias_mp)
    if st.button("Guardar Alias"):
        st.session_state.alias_mp = nuevo_alias
        guardar_datos(st.session_state.participantes, st.session_state.alias_mp, st.session_state.gastos)
        st.success("Alias actualizado correctamente.")

    st.markdown("---")
    st.subheader("Configuración de Participantes")
    nuevo_participante = st.text_input("Nombre del nuevo participante")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Agregar participante"):
            if nuevo_participante and nuevo_participante not in st.session_state.participantes:
                st.session_state.participantes.append(nuevo_participante)
                guardar_datos(st.session_state.participantes, st.session_state.alias_mp, st.session_state.gastos)
                st.success(f"Se agregó a {nuevo_participante}")
                st.rerun()
            elif nuevo_participante in st.session_state.participantes:
                st.warning("Ese participante ya existe.")
    with col2:
        if st.button("Reiniciar lista"):
            st.session_state.participantes = ["Pablo", "Gerardo", "Emanuel", "Nico"]
            guardar_datos(st.session_state.participantes, st.session_state.alias_mp, st.session_state.gastos)
            st.rerun()

    st.write("**Participantes actuales:**")
    for p in st.session_state.participantes:
        st.write(f"- {p}")

# Pestaña 2: Registrar Gasto
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
            
            st.write("**Cantidad de personas a cargo / representadas por participante:**")
            personas_cargo = {}
            cols = st.columns(min(len(st.session_state.participantes), 4) or 1)
            for idx, p in enumerate(dividir_entre):
                with cols[idx % 4]:
                    personas_
