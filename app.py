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
                alias_mp = data.get("alias_mp", "pablo.yune")
                gastos_dict = data.get("gastos", [])
                gastos = pd.DataFrame(gastos_dict)
                if gastos.empty:
                    gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])
                return participantes, alias_mp, gastos
        except:
            pass
    return ["Pablo", "Gerardo", "Emanuel", "Nico"], "pablo.yune", pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])

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
    
    # Configuración de Alias de Mercado Pago por defecto
    nuevo_alias = st.text_input("Alias de Mercado Pago (por defecto)", value=st.session_state.alias_mp)
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

# Pestaña 2: Registrar Gasto (Con selección personalizada de participantes)
with pestanas[1]:
    st.subheader("Registrar Nuevo Gasto")
    if len(st.session_state.participantes) == 0:
        st.warning("Por favor, agregue al menos un participante en la pestaña 'Participantes'.")
    else:
        with st.form("form_gasto"):
            descripcion = st.text_input("Descripción del gasto")
            monto = st.number_input("Monto total", min_value=0.0, format="%.2f")
            pagador = st.selectbox("Pagado por", st.session_state.participantes)
            
            # Permite elegir entre quiénes se divide el gasto puntualmente
            dividir_entre = st.multiselect("Dividir entre (Seleccionar participantes)", st.session_state.participantes, default=st.session_state.participantes)
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
                    guardar_datos(st.session_state.participantes, st.session_state.alias_mp, st.session_state.gastos)
                    st.success("Gasto registrado exitosamente.")
                else:
                    st.error("Por favor complete todos los campos y seleccione participantes.")

# Pestaña 1: Resumen & WhatsApp
with pestanas[0]:
    st.subheader("Resumen de Cuentas")
    if len(st.session_state.gastos) > 0:
        st.write("**Detalle de Gastos:**")
        st.dataframe(st.session_state.gastos, use_container_width=True)
        
        total_general = st.session_state.gastos["Monto"].sum()
        st.metric("Gasto Total Acumulado", f"${total_general:,.2f}")
        
        # Calcular cuánto pagó cada uno y cuánto le corresponde según los participantes seleccionados en cada gasto
        total_pagado_por = {p: 0.0 for p in st.session_state.participantes}
        total_corresponde_a = {p: 0.0 for p in st.session_state.participantes}
        
        for _, row in st.session_state.gastos.iterrows():
            pagador = row["Pagado por"]
            monto = row["Monto"]
            beneficiarios = [p.strip() for p in row["Participantes"].split(",") if p.strip() in st.session_state.participantes]
            
            if pagador in total_pagado_por:
                total_pagado_por[pagador] += monto
                
            if beneficiarios:
                cuota = monto / len(beneficiarios)
                for b in beneficiarios:
                    if b in total_corresponde_a:
                        total_corresponde_a[b] += cuota

        st.markdown("---")
        st.write("**Balance por Participante:**")
        balances_calculados = {}
        for p in st.session_state.participantes:
            pagado = total_pagado_por.get(p, 0.0)
            corresponde = total_corresponde_a.get(p, 0.0)
            diferencia = pagado - corresponde # Positivo = le deben / Negativo = debe
            balances_calculados[p] = diferencia
            
            if diferencia > 0.01:
                st.write(f"- {p}: Pagó ${pagado:,.2f} | Le corresponde pagar ${corresponde:,.2f} | Le corresponde recibir ${diferencia:,.2f}")
            elif diferencia < -0.01:
                st.write(f"- {p}: Pagó ${pagado:,.2f} | Le corresponde pagar ${corresponde:,.2f} | Debe abonar ${abs(diferencia):,.2f}")
            else:
                st.write(f"- {p}: Pagó ${pagado:,.2f} | Le corresponde pagar ${corresponde:,.2f} | Al día ($0.00)")
                
        if st.button("Eliminar último gasto"):
            st.session_state.gastos = st.session_state.gastos.iloc[:-1].reset_index(drop=True)
            guardar_datos(st.session_state.participantes, st.session_state.alias_mp, st.session_state.gastos)
            st.rerun()
            
        st.markdown("---")
        st.subheader("Enviar Detalle por WhatsApp")
        
        # Armado del mensaje formal sin iconos, con espaciado y aclaración exacta pedida
        lineas = []
        lineas.append("RESUMEN DE GASTOS COMPARTIDOS")
        lineas.append("")
        lineas.append("DETALLE DE GASTOS:")
        lineas.append("")
        
        for index, row in st.session_state.gastos.iterrows():
            lineas.append(f"- Fecha: {row['Fecha']}")
            lineas.append(f"Descripción: {row['Descripción']}")
            lineas.append(f"Pagado por: {row['Pagado por']}")
            lineas.append(f"Monto: ${row['Monto']:,.2f}")
            lineas.append(f"Dividido entre: {row['Participantes']}")
            lineas.append("")
            lineas.append("")
            
        lineas.append(f"TOTAL GENERAL: ${total_general:,.2f}")
        lineas.append("")
        lineas.append("")
        lineas.append("BALANCE POR PARTICIPANTE:")
        lineas.append("")
        
        for p in st.session_state.participantes:
            pagado = total_pagado_por.get(p, 0.0)
            corresponde = total_corresponde_a.get(p, 0.0)
            diferencia = pagado - corresponde
            
            if diferencia > 0.01:
                lineas.append(f"- {p}: Pagó ${pagado:,.2f} | Le corresponde pagar ${corresponde:,.2f} | Le corresponde recibir ${diferencia:,.2f}")
            elif diferencia < -0.01:
                lineas.append(f"- {p}: Pagó ${pagado:,.2f} | Le corresponde pagar ${corresponde:,.2f} | Debe abonar ${abs(diferencia):,.2f}")
            else:
                lineas.append(f"- {p}: Pagó ${pagado:,.2f} | Le corresponde pagar ${corresponde:,.2f} | Al día ($0.00)")
                
        lineas.append("")
        lineas.append("")
        lineas.append(f"Alias MP: {st.session_state.alias_mp}")
            
        mensaje = "\n".join(lineas)
        
        url_whatsapp = f"https://api.whatsapp.com/send?text={urllib.parse.quote(mensaje)}"
        st.markdown(f'<a href="{url_whatsapp}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer; width:100%;">Enviar por WhatsApp</button></a>', unsafe_allow_html=True)
    else:
        st.info("Aún no hay gastos registrados.")
