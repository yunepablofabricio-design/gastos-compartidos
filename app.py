import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import urllib.parse
import json
import os

st.set_page_config(page_title="Divisor de Gastos & WhatsApp", page_icon="💰", layout="centered")

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
                participantes = data.get("participantes", ["Pablo", "Gerardo", "Emanuel", "Nico"])
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
                return participantes, gastos
        except:
            pass
    p_def = [{"nombre": "Pablo", "alias": ""}, {"nombre": "Gerardo", "alias": ""}, {"nombre": "Emanuel", "alias": ""}, {"nombre": "Nico", "alias": ""}]
    return p_def, pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])

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

with pestanas[2]:
    st.subheader("Configuración de Participantes y Alias")
    
    with st.form("form_participante"):
        nuevo_participante = st.text_input("Nombre del nuevo participante")
        nuevo_alias = st.text_input("Alias de transferencia (CBU / CVU / MP)")
        submit_p = st.form_submit_button("Agregar participante")
        if submit_p:
            if nuevo_participante and nuevo_participante not in nombres_participantes:
                st.session_state.participantes.append({"nombre": nuevo_participante, "alias": nuevo_alias})
                guardar_datos(st.session_state.participantes, st.session_state.gastos)
                st.success("Se agregó a " + nuevo_participante)
                st.rerun()
            elif nuevo_participante in nombres_participantes:
                st.warning("Ese participante ya existe.")

    st.markdown("---")
    st.write("**Editar Alias de Participantes Actuales:**")
    
    for i, p in enumerate(st.session_state.participantes):
        col_a, col_b, col_c = st.columns([2, 2, 1])
        with col_a:
            st.text("Nombre: " + p['nombre'])
        with col_b:
            nuevo_alias_val = st.text_input("Alias de " + p['nombre'], value=p['alias'], key="alias_" + str(i))
            if nuevo_alias_val != p['alias']:
                st.session_state.participantes[i]['alias'] = nuevo_alias_val
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
        p_def = [{"nombre": "Pablo", "alias": ""}, {"nombre": "Gerardo", "alias": ""}, {"nombre": "Emanuel", "alias": ""}, {"nombre": "Nico", "alias": ""}]
        st.session_state.participantes = p_def
        st.session_state.gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])
        guardar_datos(st.session_state.participantes, st.session_state.gastos)
        st.rerun()

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

with pestanas[0]:
    st.subheader("Resumen de Cuentas")
    if len(st.session_state.gastos) > 0:
        st.write("**Detalle de Compras:**")
        st.dataframe(st.session_state.gastos, use_container_width=True)
        
        st.session_state.gastos["Monto"] = pd.to_numeric(st.session_state.gastos["Monto"], errors="coerce").fillna(0.0)
        total_general = float(st.session_state.gastos["Monto"].sum())
        st.metric("Gasto Total Acumulado", "$" + "{:,.2f}".format(total_general))
        
        pagado_por_persona = {p["nombre"]: 0.0 for p in st.session_state.participantes}
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
                    pagado_por_persona[pagador] += monto
                    saldos[pagador] += monto
                    detalle_personal[pagador].append("Pagó '" + desc + "' por $" + "{:,.2f}".format(monto))
                
                for b in beneficiarios:
                    saldos[b] -= cuota
                    detalle_personal[b].append("Consumió en '" + desc + "' ($" + "{:,.2f}".format(cuota) + ")")

        cant_participantes = len(nombres_participantes)
        compartido_por_persona = total_general / cant_participantes if cant_participantes > 0 else 0.0

        st.markdown("---")
        st.write("**Estado de Cuentas por Persona:**")
        
        mapa_alias = {p["nombre"]: p["alias"] for p in st.session_state.participantes}

        for p_nombre, saldo in saldos.items():
            alias_actual = mapa_alias.get(p_nombre, "")
            
            if saldo > 0.01:
                st.write("- **" + p_nombre + "**: debe recibir **$" + "{:,.2f}".format(saldo) + "** (Alias: " + (alias_actual if alias_actual else 'No configurado') + ")")
                
                msj_ind = "Hola " + p_nombre + ", este es tu resumen de gastos.\n\n"
                msj_ind += "Tu saldo a favor es de: $" + "{:,.2f}".format(saldo) + "\n"
                msj_ind += "Tus movimientos:\n"
                for item in detalle_personal[p_nombre]:
                    msj_ind += "- " + item + "\n"
                msj_ind += "\nPara que te transfieran, tu alias registrado es: " + (alias_actual if alias_actual else '[Indicar Alias]')
                
                url_ind = "https://api.whatsapp.com/send?text=" + urllib.parse.quote(msj_ind)
                st.markdown('<a href="' + url_ind + '" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:6px 12px; border-radius:4px; font-size:13px; font-weight:bold; cursor:pointer; margin-bottom:10px;">Enviar WhatsApp a ' + p_nombre + '</button></a>', unsafe_allow_html=True)

            elif saldo < -0.01:
                st.write("- **" + p_nombre + "**: debe pagar **$" + "{:,.2f}".format(abs(saldo)) + "**")
                
                msj_ind = "Hola " + p_nombre + ", este es tu resumen de gastos.\n\n"
                msj_ind += "Debes abonar la suma de: $" + "{:,.2f}".format(abs(saldo)) + "\n\n"
                msj_ind += "Tus consumos y gastos registrados:\n"
                for item in detalle_personal[p_nombre]:
                    msj_ind += "- " + item + "\n"
                
                url_ind = "https://api.whatsapp.com/send?text=" + urllib.parse.quote(msj_ind)
                st.markdown('<a href="' + url_ind + '" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:6px 12px; border-radius:4px; font-size:13px; font-weight:bold; cursor:pointer; margin-bottom:10px;">Enviar WhatsApp a ' + p_nombre + '</button></a>', unsafe_allow_html=True)
            else:
                st.write("- **" + p_nombre + "**: al día ($0.00)")
                
        if st.button("Eliminar último gasto"):
            st.session_state.gastos = st.session_state.gastos.iloc[:-1].reset_index(drop=True)
            guardar_datos(st.session_state.participantes, st.session_state.gastos)
            st.rerun()
            
        st.markdown("---")
        st.subheader("Enviar Resumen a WhatsApp")
        
        lineas = []
        lineas.append("RESUMEN DE GASTOS")
        lineas.append("")
        lineas.append("COMPRAS:")
        
        for index, row in st.session_state.gastos.iterrows():
            m_val = float(row['Monto'])
            lineas.append("  · " + str(row['Descripción']) + " ($" + "{:,.2f}".format(m_val) + " pagado por " + str(row['Pagado por']) + ")")
            
        lineas.append("")
        lineas.append("TOTAL: $" + "{:,.2f}".format(total_general))
        lineas.append("Compartido por persona: $" + "{:,.2f}".format(compartido_por_persona))
        lineas.append("")
        lineas.append("SALDOS:")
        
        for p_nombre in nombres_participantes:
            saldo = saldos.get(p_nombre, 0.0)
            gasto_ind = pagado_por_persona.get(p_nombre, 0.0)
            
            if saldo > 0.01:
                lineas.append("  · " + p_nombre + ": gastó $" + "{:,.2f}".format(gasto_ind) + " y debe recibir $" + "{:,.2f}".format(saldo))
            elif saldo < -0.01:
                if gasto_ind > 0.01:
                    lineas.append("  · " + p_nombre + ": gastó $" + "{:,.2f}".format(gasto_ind) + " y debe $" + "{:,.2f}".format(abs(saldo)))
                else:
                    lineas.append("  · " + p_nombre + ": debe $" + "{:,.2f}".format(abs(saldo)))
            else:
                lineas.append("  · " + p_nombre + ": al día")
            
        mensaje_grupo = "\n".join(lineas)
        
        url_whatsapp_grupo = "https://api.whatsapp.com/send?text=" + urllib.parse.quote(mensaje_grupo)
        st.markdown('<a href="' + url_whatsapp_grupo + '" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer; width:100%;">Enviar Resumen al Grupo</button></a>', unsafe_allow_html=True)
    else:
        st.info("Aún no hay gastos registrados.")
