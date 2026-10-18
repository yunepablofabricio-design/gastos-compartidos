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
                participantes = data.get("participantes", ["Pablo", "Mel"])
                if participantes and isinstance(participantes[0], str):
                    participantes = [{"nombre": p.strip(), "alias": ""} for p in participantes if p.strip()]
                else:
                    # Normalizar nombres quitando espacios extra
                    participantes = [{"nombre": p["nombre"].strip(), "alias": p.get("alias", "")} for p in participantes if p.get("nombre", "").strip()]
                
                gastos_dict = data.get("gastos", [])
                gastos = pd.DataFrame(gastos_dict)
                
                cols_requeridas = ["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"]
                for col in cols_requeridas:
                    if col not in gastos.columns:
                        gastos = pd.DataFrame(columns=cols_requeridas)
                        break
                if gastos.empty:
                    gastos = pd.DataFrame(columns=cols_requeridas)
                return participantes, gastos
        except:
            pass
    return [{"nombre": "Pablo", "alias": ""}, {"nombre": "Mel", "alias": ""}], pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])

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

nombres_participantes = [p["nombre"] for p in st.session_state.participantes]

# Pestaña de Participantes
with pestanas[2]:
    st.subheader("Configuración de Participantes y Alias")
    
    with st.form("form_participante"):
        nuevo_participante = st.text_input("Nombre del nuevo participante")
        nuevo_alias = st.text_input("Alias de transferencia (CBU / CVU / MP)")
        submit_p = st.form_submit_button("Agregar participante")
        if submit_p:
            nombre_limpio = nuevo_participante.strip()
            if nombre_limpio and nombre_limpio not in nombres_participantes:
                st.session_state.participantes.append({"nombre": nombre_limpio, "alias": nuevo_alias.strip()})
                guardar_datos(st.session_state.participantes, st.session_state.gastos)
                st.success("Se agregó a " + nombre_limpio)
                st.rerun()
            elif nombre_limpio in nombres_participantes:
                st.warning("Ese participante ya existe.")

    st.markdown("---")
    st.write("**Editar Alias de Participantes Actuales:**")
    
    for i, p in enumerate(st.session_state.participantes):
        col_a, col_b, col_c = st.columns([2, 2, 1])
        with col_a:
            st.text("Nombre: " + p['nombre'])
        with col_b:
            nuevo_alias_val = st.text_input("Alias de " + p['nombre'], value=p['alias'], key="alias_tab_" + str(i))
            if nuevo_alias_val != p['alias']:
                st.session_state.participantes[i]['alias'] = nuevo_alias_val.strip()
                guardar_datos(st.session_state.participantes, st.session_state.gastos)
        with col_c:
            st.write("")
            if st.button("Eliminar", key="del_" + str(i)):
                if len(st.session_state.participantes) > 1:
                    st.session_state.participantes.pop(i)
                    guardar_datos(st.session_state.participantes, st.session_state.gastos)
                    st.rerun()
                else:
                    st.error("Debe quedar al menos un participante.")

    if st.button("Reiniciar datos y lista"):
        st.session_state.participantes = [{"nombre": "Pablo", "alias": ""}, {"nombre": "Mel", "alias": ""}]
        st.session_state.gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])
        guardar_datos(st.session_state.participantes, st.session_state.gastos)
        st.rerun()

# Pestaña de Registrar Gasto
with pestanas[1]:
    st.subheader("Registrar Nuevo Gasto")
    if len(nombres_participantes) == 0:
        st.warning("Por favor, agregue al menos un participante en la pestaña 'Participantes'.")
    else:
        with st.form("form_gasto"):
            descripcion = st.text_input("Descripción del gasto")
            monto = st.number_input("Monto total", min_value=0.0, format="%.2f")
            pagador = st.selectbox("Pagado por", nombres_participantes)
            dividir_entre = st.multiselect("Dividir entre", nombres_participantes, default=nombres_participantes)
            fecha = st.date_input("Fecha", datetime.now())
            
            submit = st.form_submit_button("Guardar Gasto")
            if submit:
                if descripcion and monto > 0 and dividir_entre:
                    nuevo_gasto = pd.DataFrame({
                        "Fecha": [fecha.strftime("%Y-%m-%d")],
                        "Descripción": [descripcion],
                        "Pagado por": [pagador],
                        "Monto": [float(monto)],
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
    
    with st.expander("Modificar Alias de Participantes"):
        for i, p in enumerate(st.session_state.participantes):
           alias_rapido = st.text_input("Alias para " + p['nombre'], value=p['alias'], key="alias_res_" + str(i))
