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
                participantes = data.get("participantes", [])
                if participantes and isinstance(participantes[0], str):
                    participantes = [{"nombre": p, "alias": ""} for p in participantes]
                
                gastos_dict = data.get("gastos", [])
                gastos = pd.DataFrame(gastos_dict)
                
                alias_grupo = data.get("alias_grupo", "pabloyune")
                
                cols_requeridas = ["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"]
                for col in cols_requeridas:
                    if col not in gastos.columns:
                        gastos = pd.DataFrame(columns=cols_requeridas)
                        break
                if gastos.empty:
                    gastos = pd.DataFrame(columns=cols_requeridas)
                
                if participantes:
                    return participantes, gastos, alias_grupo
        except:
            pass
            
    def_part = [
        {"nombre": "Pablo", "alias": ""},
        {"nombre": "Gerardo", "alias": ""},
        {"nombre": "Emanuel", "alias": ""},
        {"nombre": "Nico", "alias": ""}
    ]
    return def_part, pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"]), "pabloyune"

def guardar_datos(participantes, gastos, alias_grupo):
    data = {
        "participantes": participantes,
        "gastos": gastos.to_dict(orient="records"),
        "alias_grupo": alias_grupo
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'participantes' not in st.session_state or 'gastos' not in st.session_state:
    p, g, ag = cargar_datos()
    st.session_state.participantes = p
    st.session_state.gastos = g
    st.session_state.alias_grupo = ag

pestanas = st.tabs(["📊 Resumen & WhatsApp", "💸 Registrar Gasto", "👥 Participantes"])

nombres_participantes = [p["nombre"] for p in st.session_state.participantes]

with pestanas[2]:
    st.subheader("Configuración de Participantes")
    
    with st.form("form_participante"):
        nuevo_participante = st.text_input("Nombre del nuevo participante")
        submit_p = st.form_submit_button("Agregar participante")
        if submit_p:
            if nuevo_participante and nuevo_participante not in nombres_participantes:
                st.session_state.participantes.append({"nombre": nuevo_participante.strip(), "alias": ""})
                guardar_datos(st.session_state.participantes, st.session_state.gastos, st.session_state.alias_grupo)
                st.success(f"Se agregó a {nuevo_participante}")
                st.rerun()
            elif nuevo_participante in nombres_participantes:
                st.warning("Ese participante ya existe.")

    st.markdown("---")
    st.write("**Lista de Participantes Actuales:**")
    
    for i, p in enumerate(st.session_state.participantes):
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.text("Nombre: " + p['nombre'])
        with col_b:
            if st.button("Eliminar", key="del_" + str(i)):
                if len(st.session_state.participantes) > 1:
                    st.session_state.participantes.pop(i)
                    guardar_datos(st.session_state.participantes, st.session_state.gastos, st.session_state.alias_grupo)
                    st.rerun()
                else:
                    st.error("Debe quedar al menos un participante.")

    if st.button("Reiniciar datos y lista"):
        st.session_state.participantes = [
            {"nombre": "Pablo", "alias": ""},
            {"nombre": "Gerardo", "alias": ""},
            {"nombre": "Emanuel", "alias": ""},
            {"nombre": "Nico", "alias": ""}
        ]
        st.session_state.gastos = pd.DataFrame(columns=["Fecha", "Descripción", "Pagado por", "Monto", "Participantes"])
        st.session_state.alias_grupo = "pabloyune"
        guardar_datos(st.session_state.participantes, st.session_state.gastos, st.session_state.alias_grupo)
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
                    guardar_datos(st.session_state.participantes, st.session_state.gastos, st.session_state.alias_grupo)
                    st.success("Gasto registrado exitosamente.")
                else:
                    st.error("Por favor complete todos los campos y seleccione participantes.")

with pestanas[0]:
    st.subheader("Resumen de Cuentas")
    
    # Campo rápido para cambiar el Alias de transferencia del grupo actual
    nuevo_alias_grupo = st.text_input("💳 Alias para transferir (modificable según el grupo/viaje):", value=st.session_state.alias_grupo)
    if nuevo_alias_grupo != st.session_state.alias_grupo:
        st.session_state.alias_grupo = nuevo_alias_grupo.strip()
        guardar_datos(st.session_state.participantes, st.session_state.gastos, st.session_state.alias_grupo)

    if len(st.session_state.gastos) > 0:
        st.write("**Detalle de Compras (puedes borrar un gasto específico):**")
        
        gastos_a_borrar = None
        for idx, row in st.session_state.gastos.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 3, 1])
            with col1:
                st.write(f"**{row['Descripción']}**")
            with col2:
                st.write(f"${float(row['Monto']):,.2f}")
            with col3:
                st.write(f"Pagó: {row['Pagado por']}")
            with col4:
                st.write(f"({row['Participantes']})")
            with col5:
                if st.button("❌", key=f"del_gasto_{idx}"):
                    gastos_a_borrar = idx

        if gastos_a_borrar is not None:
            st.session_state.gastos = st.session_state.gastos.drop(index=gastos_a_borrar).reset_index(drop=True)
            guardar_datos(st.session_state.participantes, st.session_state.gastos, st.session_state.alias_grupo)
            st.rerun()

        st.markdown("---")
        st.session_state.gastos["Monto"] = pd.to_numeric(st.session_state.gastos["Monto"], errors="coerce").fillna(0.0)
        total_general = float(st.session_state.gastos["Monto"].sum())
        st.metric("Gasto Total Acumulado", "$" + f"{total_general:,.2f}")
        
        saldos = {p["nombre"]: 0.0 for p in st.session_state.participantes}
        pagos_por_persona = {p["nombre"]: 0.0 for p in st.session_state.participantes}
        consumos_por_persona = {p["nombre"]: 0.0 for p in st.session_state.participantes}
        
        for _, row in st.session_state.gastos.iterrows():
            pagador = str(row["Pagado por"]).strip()
            monto = float(row["Monto"])
            part_str = str(row["Participantes"])
            beneficiarios = [p.strip() for p in part_str.split(",") if p.strip() in saldos]
            
            if pagador in pagos_por_persona:
                pagos_por_persona[pagador] += monto
                saldos[pagador] += monto
                
            if beneficiarios:
                cuota = monto / len(beneficiarios)
                for b in beneficiarios:
                    consumos_por_persona[b] += cuota
                    saldos[b] -= cuota

        st.markdown("---")
        st.subheader("Enviar Resumen al Grupo de WhatsApp")
        
        personas_en_gastos = set()
        for _, r in st.session_state.gastos.iterrows():
            part_list = [p.strip() for p in str(r['Participantes']).split(",") if p.strip()]
            personas_en_gastos.update(part_list)
            if str(r['Pagado por']).strip():
                personas_en_gastos.add(str(r['Pagado por']).strip())
        
        lineas = []
        lineas.append("RESUMEN DE GASTOS")
        lineas.append("")
        lineas.append("COMPRAS:")
        
        total_compartidos = 0.0
        total_extras = 0.0
        
        for index, row in st.session_state.gastos.iterrows():
            monto_row = float(row['Monto'])
            part_raw = [p.strip() for p in str(row['Participantes']).split(",") if p.strip()]
            
            if set(part_raw) == personas_en_gastos:
                etiqueta_part = "(Todos)"
                total_compartidos += monto_row
            else:
                etiqueta_part = f"({'/'.join(part_raw)})"
                total_extras += monto_row
                
            lineas.append(f"· {row['Descripción']} (${monto_row:,.2f} pagado por {row['Pagado por']}) {etiqueta_part}")
            
        lineas.append("")
        lineas.append(f"TOTAL DE GASTOS COMPARTIDOS: ${total_compartidos:,.2f}")
        
        cant_personas = len(personas_en_gastos) if personas_en_gastos else len(st.session_state.participantes)
        lineas.append(f"Compartido por persona: ${(total_compartidos / cant_personas):,.2f}")
        
        if total_extras > 0:
            lineas.append(f"TOTAL DE GASTOS EXTRAS: ${total_extras:,.2f}")
            
        lineas.append("")
        
        lineas.append("SALDOS:")
        for p_nombre, saldo in saldos.items():
            if p_nombre in personas_en_gastos:
                gasto_total_persona = pagos_por_persona.get(p_nombre, 0.0)
                
                consumo_extra_persona = 0.0
                for _, r in st.session_state.gastos.iterrows():
                    part_raw = [p.strip() for p in str(r['Participantes']).split(",") if p.strip()]
                    if set(part_raw) != personas_en_gastos and p_nombre in part_raw:
                        consumo_extra_persona += float(r['Monto']) / len(part_raw)
                
                extra_txt = f" (tiene extra de ${consumo_extra_persona:,.2f})" if consumo_extra_persona > 0 else ""
                
                if saldo > 0.01:
                    lineas.append(f"· {p_nombre}: gastó ${gasto_total_persona:,.2f} y debe recibir ${saldo:,.2f}{extra_txt}")
                elif saldo < -0.01:
                    if gasto_total_persona > 0:
                        lineas.append(f"· {p_nombre}: gastó ${gasto_total_persona:,.2f} y debe ${abs(saldo):,.2f}{extra_txt}")
                    else:
                        lineas.append(f"· {p_nombre}: debe ${abs(saldo):,.2f}{extra_txt}")

        lineas.append("")
        lineas.append("ALIAS PARA TRANSFERIR:")
        if st.session_state.alias_grupo:
            lineas.append(f"· {st.session_state.alias_grupo}")
            
        mensaje_grupo = "\n".join(lineas)
        
        st.markdown("**Vista previa del mensaje para el grupo:**")
        st.code(mensaje_grupo, language="text")
        
        url_whatsapp_grupo = "https://api.whatsapp.com/send?text=" + urllib.parse.quote(mensaje_grupo)
        st.markdown('<a href="' + url_whatsapp_grupo + '" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer; width:100%;">Enviar Resumen al Grupo de WhatsApp</button></a>', unsafe_allow_html=True)
    else:
        st.info("Aún no hay gastos registrados.")
