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
                alias_general = data.get("alias_general", "")
                
                if participantes and isinstance(participantes[0], str):
                    participantes = [{"nombre": p, "alias": ""} for p in participantes]
                
                gastos_dict = data.get("gastos", [])
                gastos = pd.DataFrame(gastos_dict)
                
                cols_requeridas = ["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"]
                for col in cols_requeridas:
                    if col not in gastos.columns:
                        gastos = pd.DataFrame(columns=cols_requeridas)
                        break
                if gastos.empty:
                    gastos = pd.DataFrame(columns=cols_requeridas)
                return participantes, gastos, alias_general
        except:
            pass
    return [{"nombre": "Pablo", "alias": ""}, {"nombre": "Mel", "alias": ""}], pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"]), ""

def guardar_datos(participantes, gastos, alias_general):
    data = {
        "participantes": participantes,
        "gastos": gastos.to_dict(orient="records"),
        "alias_general": alias_general
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'participantes' not in st.session_state or 'gastos' not in st.session_state or 'alias_general' not in st.session_state:
    p, g, a = cargar_datos()
    st.session_state.participantes = p
    st.session_state.gastos = g
    st.session_state.alias_general = a

pestanas = st.tabs(["📊 Resumen & WhatsApp", "💸 Registrar Gasto", "👥 Participantes"])

nombres_participantes = [p["nombre"] for p in st.session_state.participantes]

# Pestaña de Participantes
with pestanas[2]:
    st.subheader("Configuración de Participantes")
    
    with st.form("form_participante"):
        nuevo_participante = st.text_input("Nombre del nuevo participante")
        submit_p = st.form_submit_button("Agregar participante")
        if submit_p:
            if nuevo_participante and nuevo_participante not in nombres_participantes:
                st.session_state.participantes.append({"nombre": nuevo_participante, "alias": ""})
                guardar_datos(st.session_state.participantes, st.session_state.gastos, st.session_state.alias_general)
                st.success("Se agregó a " + nuevo_participante)
                st.rerun()
            elif nuevo_participante in nombres_participantes:
                st.warning("Ese participante ya existe.")

    st.markdown("---")
    st.write("**Lista de Participantes:**")
    
    for i, p in enumerate(st.session_state.participantes):
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.text("Nombre: " + p['nombre'])
        with col_b:
            if st.button("Eliminar", key="del_" + str(i)):
                if len(st.session_state.participantes) > 1:
                    st.session_state.participantes.pop(i)
                    guardar_datos(st.session_state.participantes, st.session_state.gastos, st.session_state.alias_general)
                    st.rerun()
                else:
                    st.error("Debe quedar al menos un participante.")

    if st.button("Reiniciar datos y lista"):
        st.session_state.participantes = [{"nombre": "Pablo", "alias": ""}, {"nombre": "Mel", "alias": ""}]
        st.session_state.gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])
        st.session_state.alias_general = ""
        guardar_datos(st.session_state.participantes, st.session_state.gastos, st.session_state.alias_general)
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
                    guardar_datos(st.session_state.participantes, st.session_state.gastos, st.session_state.alias_general)
                    st.success("Gasto registrado exitosamente.")
                else:
                    st.error("Por favor complete todos los campos y seleccione participantes.")

# Pestaña de Resumen & WhatsApp
with pestanas[0]:
    st.subheader("Resumen de Cuentas")
    
    # Campo para modificar el Alias fácilmente desde la app
    alias_input = st.text_input("Configurar Alias para transferencias (ej: viaje.amigos.mp)", value=st.session_state.alias_general)
    if alias_input != st.session_state.alias_general:
        st.session_state.alias_general = alias_input
        guardar_datos(st.session_state.participantes, st.session_state.gastos, st.session_state.alias_general)
        st.success("Alias actualizado correctamente.")

    st.markdown("---")

    if len(st.session_state.gastos) > 0:
        st.write("**Detalle de Compras:**")
        st.dataframe(st.session_state.gastos, use_container_width=True)
        
        st.session_state.gastos["Monto"] = pd.to_numeric(st.session_state.gastos["Monto"], errors="coerce").fillna(0.0)
        total_general = st.session_state.gastos["Monto"].sum()
        st.metric("Gasto Total Acumulado", "$" + f"{total_general:,.2f}")
        
        saldos = {p["nombre"]: 0.0 for p in st.session_state.participantes}
        detalle_personal = {p["nombre"]: [] for p in st.session_state.participantes}
        
        for _, row in st.session_state.gastos.iterrows():
            pagador = str(row["Pagado por"])
            monto = float(row["Monto"])
            desc = str(row["Descripción"])
            part_str = str(row["Participantes"])
            beneficiarios = [p.strip() for p in part_str.split(",") if p.strip() in saldos]
            
            if beneficiarios:
                cuota = monto / len(beneficiarios)
                if pagador in saldos:
                    saldos[pagador] += monto
                    detalle_personal[pagador].append("Pagó '" + desc + "' por $" + f"{monto:,.2f}")
                
                for b in beneficiarios:
                    saldos[b] -= cuota
                    detalle_personal[b].append("Consumió en '" + desc + "' ($" + f"{cuota:,.2f}" + ")")

        st.markdown("---")
        st.write("**Estado de Cuentas por Persona:**")

        for p_nombre, saldo in saldos.items():
            if saldo > 0.01:
                st.write("- **" + p_nombre + "**: recupera **$" + f"{saldo:,.2f}" + "**")
            elif saldo < -0.01:
                st.write("- **" + p_nombre + "**: debe **$" + f"{abs(saldo):,.2f}" + "**")
            else:
                st.write("- **" + p_nombre + "**: al día ($0.00)")
                
        if st.button("Eliminar último gasto"):
            st.session_state.gastos = st.session_state.gastos.iloc[:-1].reset_index(drop=True)
            guardar_datos(st.session_state.participantes, st.session_state.gastos, st.session_state.alias_general)
            st.rerun()
            
        st.markdown("---")
        st.subheader("Enviar Resumen por WhatsApp")
        
        # Construcción del mensaje final para el grupo
        lineas = []
        lineas.append("RESUMEN GENERAL DE GASTOS")
        lineas.append("")
        
        for p_nombre, saldo in saldos.items():
            if saldo > 0.01:
                lineas.append("- " + p_nombre + ": Recupera $" + f"{saldo:,.2f}")
            elif saldo < -0.01:
                lineas.append("- " + p_nombre + ": Debe $" + f"{abs(saldo):,.2f}")
            else:
                lineas.append("- " + p_nombre + ": Al día ($0.00)")
            
        lineas.append("")
        if st.session_state.alias_general:
            lineas.append("Alias MP: " + st.session_state.alias_general)
        else:
            lineas.append("Alias MP: [Sin configurar]")
            
        mensaje_grupo = "\n".join(lineas)
        
        url_whatsapp_grupo = "https://api.whatsapp.com/send?text=" + urllib.parse.quote(mensaje_grupo)
        st.markdown('<a href="' + url_whatsapp_grupo + '" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer; width:100%;">Enviar Resumen a WhatsApp</button></a>', unsafe_allow_html=True)
    else:
        st.info("Aún no hay gastos registrados.")
