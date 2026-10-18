import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import urllib.parse
import json
import os

st.set_page_config(page_title="Divisor de Gastos App", page_icon="💸", layout="centered")

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
                participantes = data.get("participantes", ["Pablo", "Mel"])
                gastos_dict = data.get("gastos", [])
                gastos = pd.DataFrame(gastos_dict)
                if gastos.empty:
                    gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])
                return participantes, gastos
        except:
            pass
    return ["Pablo", "Mel"], pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])

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

pestanas = st.tabs(["Resumen & WhatsApp", "Registrar Gasto", "Participantes"])

# Pestaña 3: Participantes
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
            st.session_state.participantes = ["Pablo", "Mel"]
            guardar_datos(st.session_state.participantes, st.session_state.gastos)
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
            dividir_entre
