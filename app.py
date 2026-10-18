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

def normalizar_participantes(raw_list):
    resultado = []
    for item in raw_list:
        if isinstance(item, str):
            resultado.append({"nombre": item})
        elif isinstance(item, dict) and "nombre" in item:
            resultado.append({"nombre": item["nombre"]})
    return resultado if resultado else [
        {"nombre": "Pablo"},
        {"nombre": "Gerardo"},
        {"nombre": "Emanuel"},
        {"nombre": "Nico"}
    ]

def cargar_datos():
    participantes_def = [
        {"nombre": "Pablo"},
        {"nombre": "Gerardo"},
        {"nombre": "Emanuel"},
        {"nombre": "Nico"}
    ]
    alias_central_def = "pabloyune"
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                participantes_raw = data.get("participantes", [])
                participantes = normalizar_participantes(participantes_raw)
                alias_central = data.get("alias_central", alias_central_def)
                
                gastos_dict = data.get("gastos", [])
                gastos = pd.DataFrame(gastos_dict)
                if gastos.empty or not set(["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"]).issubset(gastos.columns):
                    gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])
                return participantes, alias_central, gastos
        except Exception:
            pass
    return participantes_def, alias_central_def, pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])

def guardar_datos(participantes, alias_central, gastos):
    data = {
        "participantes": participantes,
        "alias_central": alias_central,
        "gastos": gastos.to_dict(orient="records")
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'participantes' not in st.session_state or 'gastos' not in st.session_state or 'alias_central' not in st.session_state:
    p, ac, g = cargar_datos()
    st.session_state.participantes = p
    st.session_state.alias_central = ac
    st.session_state.gastos = g

pestanas = st.tabs(["Resumen & WhatsApp", "Registrar Gasto", "Participantes"])

nombres_participantes = [p["nombre"] for p in st.session_state.participantes]

# Pestaña 3: Participantes y Alias Único
with pestanas[2]:
    st.subheader("Configuración de Participantes y Alias de Transferencia")
    
    # Campo para el alias único central
    nuevo_alias_central = st.text_input("Alias único para recibir transferencias (MP / CBU / CVU)", value=st.session_state.alias_central)
    if nuevo_alias_central != st.session_state.alias_central:
        st.session_state.alias_central = nuevo_alias_central
        guardar_datos(st.session_state.participantes, st.session_state.alias_central, st.session_state.gastos)
        st.success("Alias actualizado correctamente.")
    
    st.markdown("---")
    
    with st.form("form_participante"):
        nuevo_participante = st.text_input("Nombre del nuevo participante")
        submit_p = st.form_submit_button("Agregar participante")
        if submit_p:
            if nuevo_participante and nuevo_participante not in nombres_participantes:
                st.session_state.participantes.append({"nombre": nuevo_participante})
                guardar_datos(st.session_state.participantes, st.session_state.alias_central, st.session_state.gastos)
                st.success(f"Se agregó a {nuevo_participante}")
                st.rerun()
            elif nuevo_participante in nombres_participantes:
                st.warning("Ese participante ya existe.")

    st.markdown("---")
    st.write("**Lista de Participantes Actuales:**")
    
    for i, p in enumerate(st.session_state.participantes):
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.text(f"• {p['nombre']}")
        with col_b:
            if st.button("Eliminar", key=f"del_{i}"):
                if len(st.session_state.participantes) > 1:
                    st.session_state.participantes.pop(i)
                    guardar_datos(st.session_state.participantes, st.session_state.alias_central, st.session_state.gastos)
                    st.rerun()
                else:
                    st.error("Debe quedar al menos un participante.")

    if st.button("Reiniciar lista por defecto"):
        st.session_state.participantes = [
            {"nombre": "Pablo"},
            {"nombre": "Gerardo"},
            {"nombre": "Emanuel"},
            {"nombre": "Nico"}
        ]
        st.session_state.alias_central = "pabloyune"
        guardar_datos(st.session_state.participantes, st.session_state.alias_central, st.session_state.gastos)
        st.rerun()

# Pestaña 2: Registrar Gasto
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
                        "Monto": [monto],
                        "Participantes": [", ".join(dividir_entre)]
                    })
                    st.session_state.gastos = pd.concat([st.session_state.gastos, nuevo_gasto], ignore_index=True)
                    guardar_datos(st.session_state.participantes, st.session_state.alias_central, st.session_state.gastos)
                    st.success("Gasto registrado exitosamente.")
                else:
                    st.error("Por favor complete todos los campos y seleccione participantes.")

# Pestaña 1: Resumen & WhatsApp
with pestanas[0]:
    st.subheader("Resumen de Cuentas")
    if len(st.session_state.gastos) > 0:
        st.write("**Detalle de Compras:**")
        st.dataframe(st.session_state.gastos, use_container_width=True)
        
        total_general = st.session_state.gastos["Monto"].sum()
        st.metric("Gasto Total Acumulado", f"${total_general:,.2f}")
        
        num_participantes_total = len(st.session_state.participantes)
        costo_promedio_persona = total_general / num_participantes_total if num_participantes_total > 0 else 0

        saldos = {p["nombre"]: 0.0 for p in st.session_state.participantes}
        total_pagado_por_persona = {p["nombre"]: 0.0 for p in st.session_state.participantes}
        gastos_compartidos_persona = {p["nombre"]: 0.0 for p in st.session_state.participantes}
        gastos_extras_persona = {p["nombre"]: 0.0 for p in st.session_state.participantes}
        detalle_personal = {p["nombre"]: [] for p in st.session_state.participantes}
        
        for _, row in st.session_state.gastos.iterrows():
            pagador = row["Pagado por"]
            monto = float(row["Monto"])
            desc = str(row["Descripción"])
            beneficiarios = [p.strip() for p in str(row["Participantes"]).split(",") if p.strip() in saldos]
            
            if pagador in total_pagado_por_persona:
                total_pagado_por_persona[pagador] += monto

            if beneficiarios:
                cuota = monto / len(beneficiarios)
                es_extra = len(beneficiarios) < num_participantes_total
                
                if pag
