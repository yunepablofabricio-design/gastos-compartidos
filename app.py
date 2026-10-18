import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np

st.set_page_config(page_title="Divisor de Gastos App", page_icon="💸", layout="centered")

st.markdown("""
<style>
    .main {background-color: #F8FAFC;}
    .stButton>button {width: 100%; border-radius: 8px; font-weight: bold;}
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.title("💸 Divisor de Gastos & WhatsApp")
st.write("Gestioná gastos compartidos, individuales y detalles exactos.")

if 'participants' not in st.session_state:
    st.session_state['participants'] = [
        {"name": "Juan", "shares": 1},
        {"name": "Pedro", "shares": 1},
        {"name": "Lucas", "shares": 1},
        {"name": "María", "shares": 1}
    ]

if 'expenses' not in st.session_state:
    st.session_state['expenses'] = [
        {
            "date": "2026-10-10", 
            "concept": "Supermercado inicial", 
            "payer": "Juan", 
            "type": "TODOS", 
            "amount": 40000.0, 
            "participants": ["Juan", "Pedro", "Lucas", "María"]
        }
    ]

tab1, tab2, tab3 = st.tabs(["📊 Resumen & WhatsApp", "💸 Registrar Gasto", "👥 Participantes"])

participant_names = [p["name"] for p in st.session_state['participants']]
total_shares = sum([p["shares"] for p in st.session_state['participants']])

def calculate_accounts():
    accounts = {p["name"]: {"shares": p["shares"], "paid": 0.0, "common": 0.0, "extras": 0.0, "details": []} for p in st.session_state['participants']}
    
    total_todos = sum([e["amount"] for e in st.session_state['expenses'] if e["type"] == "TODOS"])
    base_quota_per_share = total_todos / total_shares if total_shares > 0 else 0.0

    for p in accounts:
        accounts[p]["common"] = accounts[p]["shares"] * base_quota_per_share

    for e in st.session_state['expenses']:
        payer = e["payer"]
        amt = e["amount"]
        concept = e["concept"]
        exp_type = e["type"]
        parts = e["participants"]
        
        if payer in accounts:
            accounts[payer]["paid"] += amt
            accounts[payer]["details"].append(f"• Pagaste '{concept}': ${amt:,.2f}")
        
        if exp_type == "TODOS":
            pass
        elif exp_type == "COMPARTIDO":
            n_parts = len(parts)
            if n_parts > 0:
                per_person = amt / n_parts
                for p in parts:
                    if p in accounts:
                        accounts[p]["extras"] += per_person
        else:
            if exp_type in accounts:
                accounts[exp_type]["extras"] += amt

    summary_data = []
    for p, data in accounts.items():
        total_consumption = data["common"] + data["extras"]
        balance = data["paid"] - total_consumption
        summary_data.append({
            "Participante": p,
            "Cupos": data["shares"],
            "Aportó": data["paid"],
            "Gasto Común": data["common"],
            "Gastos Extras": data["extras"],
            "Consumo Total": total_consumption,
            "Saldo": balance,
            "Detalles": data["details"]
        })
    return pd.DataFrame(summary_data)

df_summary = calculate_accounts()

with tab1:
    st.subheader("📋 Estado de Cuentas General")
    if not df_summary.empty:
        display_df = df_summary[["Participante", "Cupos", "Aportó", "Gasto Común", "Gastos Extras", "Consumo Total", "Saldo"]].copy()
        display_df["Aportó"] = display_df["Aportó"].apply(lambda x: f"${x:,.2f}")
        display_df["Gasto Común"] = display_df["Gasto Común"].apply(lambda x: f"${x:,.2f}")
        display_df["Gastos Extras"] = display_df["Gastos Extras"].apply(lambda x: f"${x:,.2f}")
        display_df["Consumo Total"] = display_df["Consumo Total"].apply(lambda x: f"${x:,.2f}")
        display_df["Saldo"] = display_df["Saldo"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(display_df, use_container_width=True)
        
        global_msg = "*RESUMEN GENERAL DE GASTOS*\n\n"
        for _, row in df_summary.iterrows():
            p_name = row["Participante"]
            p_saldo = row["Saldo"]
            if p_saldo > 0:
                estado = f"Tiene que recuperar *${p_saldo:,.2f}*"
            elif p_saldo < 0:
                estado = f"Tiene que transferir *${abs(p_saldo):,.2f}*"
            else:
                estado = "Está al día ($0)"
            global_msg += f"• *{p_name}*: {estado}\n"
        global_msg += "\nAlias MP: `viaje.amigos.mp`"
        
        st.markdown("---")
        st.subheader("📢 Resumen Grupal para WhatsApp")
        
        copy_group_html = f"""
        <div style="font-family: sans-serif;">
            <textarea id="group_box" style="width:100%; height:130px; border-radius:8px; padding:10px; border:1px solid #cbd5e1; font-size:14px; background-color:#f8fafc;">{global_msg}</textarea>
            <button onclick="navigator.clipboard.writeText(document.getElementById('group_box').value); alert('¡Resumen grupal copiado al portapapeles!');" style="background-color:#1E3A8A; color:white; padding:12px; border:none; border-radius:8px; width:100%; font-weight:bold; font-size:15px; cursor:pointer; margin-top:8px; margin-bottom: 8px;">
                📋 Copiar Resumen Grupal
            </button>
            <a href="https://api.whatsapp.com/send?text={global_msg}" target="_blank" style="text-decoration:none;">
                <button style="background-color:#22C55E; color:white; padding:12px; border:none; border-radius:8px; width:100%; font-weight:bold; font-size:15px; cursor:pointer;">
                    💬 Enviar Resumen al Grupo por WhatsApp
                </button>
            </a>
        </div>
        """
        components.html(copy_group_html, height=240)

        st.markdown("---")
        st.subheader("📜 Historial Detallado de Gastos para WhatsApp")
        
        # Formato formal sin iconos ni tipo de gasto
        historial_msg = "*HISTORIAL DE GASTOS REGISTRADOS*\n\n"
        for idx, exp in enumerate(st.session_state['expenses'], 1):
            historial_msg += f"{idx}. *{exp['concept']}* (${exp['amount']:,.2f})\n   Fecha: {exp['date']} | Pagó: {exp['payer']}\n\n"
        
        copy_hist_html = f"""
        <div style="font-family: sans-serif;">
            <textarea id="hist_box" style="width:100%; height:130px; border-radius:8px; padding:10px; border:1px solid #cbd5e1; font-size:14px; background-color:#f8fafc;">{historial_msg}</textarea>
            <button onclick="navigator.clipboard.writeText(document.getElementById('hist_box').value); alert('¡Historial de gastos copiado al portapapeles!');" style="background-color:#475569; color:white; padding:12px; border:none; border-radius:8px; width:100%; font-weight:bold; font-size:15px; cursor:pointer; margin-top:8px; margin-bottom: 8px;">
                📋 Copiar Historial de Gastos
            </button>
            <a href="https://api.whatsapp.com/send?text={historial_msg}" target="_blank" style="text-decoration:none;">
                <button style="background-color:#22C55E; color:white; padding:12px; border:none; border-radius:8px; width:100%; font-weight:bold; font-size:15px; cursor:pointer;">
                    💬 Enviar Historial al Grupo por WhatsApp
                </button>
            </a>
        </div>
        """
        components.html(copy_hist_html, height=240)
    
    st.markdown("---")
    st.subheader("📱 Detalle Individual para WhatsApp")
    
    selected_person = st.selectbox("Seleccioná la persona:", participant_names, key="select_person_whatsapp")
    
    if selected_person and not df_summary.empty:
        p_row = df_summary[df_summary["Participante"] == selected_person].iloc[0]
        common_val = p_row["Gasto Común"]
        extras_val = p_row["Gastos Extras"]
        total_consumption = p_row["Consumo Total"]
        paid_val = p_row["Aportó"]
        balance = p_row["Saldo"]
        user_details = p_row["Detalles"]
        
        detalle_compras_str = "\n".join(user_details) if user_details else "• Sin compras directas registradas."
        
        if balance < 0:
            monto_accion = abs(balance)
            accion_texto = f"TOTAL A TRANSFERIR: *${monto_accion:,.2f}*\nAlias MP: `viaje.amigos.mp`"
            titulo_tarjeta = f"DETALLE DE {selected_person.upper()} (DEBE TRANSFERIR)"
        elif balance > 0:
            monto_accion = balance
            accion_texto = f"TOTAL A RECUPERAR: *${monto_accion:,.2f}* (Te lo tienen que transferir)"
            titulo_tarjeta = f"DETALLE DE {selected_person.upper()} (TIENE QUE RECUPERAR)"
        else:
            monto_accion = 0.0
            accion_texto = "ESTÁS AL DÍA: No tenés que poner ni recuperar nada."
            titulo_tarjeta = f"DETALLE DE {selected_person.upper()} (ESTÁ AL DÍA)"

        whatsapp_msg = (
            f"Hola *{selected_person}*, acá tenés el detalle de tu cuenta:\n\n"
            f"Gasto Común: ${common_val:,.2f}\n"
            f"Gastos Extras: ${extras_val:,.2f}\n"
            f"Consumo Total: ${total_consumption:,.2f}\n\n"
            f"Lo que pusiste: ${paid_val:,.2f}\n"
            f"Desglose:\n{detalle_compras_str}\n\n"
            f"{accion_texto}"
        )

        st.markdown(f"""
        <div class="card" style="background-color: #EFF6FF; border: 2px solid #1E3A8A;">
            <h3 style="color: #1E3A8A; text-align: center;">{titulo_tarjeta}</h3>
            <p><b>Gasto Común:</b> ${common_val:,.2f}</p>
            <p><b>Gastos Extras:</b> ${extras_val:,.2f}</p>
            <p><b>Consumo Total:</b> ${total_consumption:,.2f}</p>
            <hr>
            <p><b>Lo que pagaste:</b> ${paid_val:,.2f}</p>
            {''.join([f'<p style="margin-left:15px; font-size:14px;">{d}</p>' for d in user_details]) if user_details else '<p style="margin-left:15px; font-size:14px;">Sin compras registradas.</p>'}
            <hr>
            <h3 style="color: #991B1B; text-align: center;">{accion_texto.replace('*', '')}</h3>
        </div>
        """, unsafe_allow_html=True)

        copy_ind_html = f"""
        <div style="font-family: sans-serif;">
            <textarea id="ind_box" style="width:100%; height:140px; border-radius:8px; padding:10px; border:1px solid #cbd5e1; font-size:14px; background-color:#f8fafc;">{whatsapp_msg}</textarea>
            <button onclick="navigator.clipboard.writeText(document.getElementById('ind_box').value); alert('¡Detalle de {selected_person} copiado al portapapeles!');" style="background-color:#1E3A8A; color:white; padding:12px; border:none; border-radius:8px; width:100%; font-weight:bold; font-size:15px; cursor:pointer; margin-top:8px; margin-bottom: 8px;">
                📋 Copiar Detalle de {selected_person}
            </button>
            <a href="https://api.whatsapp.com/send?text={whatsapp_msg}" target="_blank" style="text-decoration:none;">
                <button style="background-color:#22C55E; color:white; padding:12px; border:none; border-radius:8px; width:100%; font-weight:bold; font-size:15px; cursor:pointer;">
                    💬 Enviar al chat individual por WhatsApp
                </button>
            </a>
        </div>
        """
        components.html(copy_ind_html, height=250)

with tab2:
    st.subheader("➕ Registrar Nuevo Gasto")
    
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Fecha")
        payer = st.selectbox("Pagado Por", participant_names, key="payer_select_reg")
    with col2:
        amount = st.number_input("Monto Total ($)", min_value=0.0, step=100.0, key="amount_input_reg")
        expense_type = st.selectbox("¿A quiénes aplica?", ["TODOS", "COMPARTIDO"] + participant_names, key="type_select_reg")
    
    concept = st.text_input("Concepto / Detalle", placeholder="Ej. Asado, Nafta, Supermercado", key="concept_input_reg")
    
    selected_participants = []
    if expense_type == "COMPARTIDO":
        st.write("👥 **Seleccioná quiénes participan de este gasto:**")
        cols = st.columns(len(participant_names))
        for idx, p in enumerate(participant_names):
            with cols[idx]:
                if st.checkbox(p, value=True, key=f"chk_shared_{p}"):
                    selected_participants.append(p)
    
    if st.button("💾 Guardar Gasto Registrado", key="btn_save_expense"):
        if concept and amount > 0:
            new_exp = {
                "date": str(date),
                "concept": concept,
                "payer": payer,
                "type": expense_type,
                "amount": amount,
                "participants": selected_participants if expense_type == "COMPARTIDO" else []
            }
            st.session_state['expenses'].append(new_exp)
            st.success("¡Gasto registrado con éxito!")
            st.rerun()
        else:
            st.error("Por favor completa el concepto y un monto mayor a 0.")

    st.markdown("---")
    st.subheader("📜 Historial de Gastos")
    if st.session_state['expenses']:
        df_exp = pd.DataFrame(st.session_state['expenses'])
        st.dataframe(df_exp, use_container_width=True)
        
        if st.button("🗑️ Borrar último gasto", key="btn_del_last_exp"):
            st.session_state['expenses'].pop()
            st.rerun()

with tab3:
    st.subheader("👥 Gestión de Participantes y Cupos")
    with st.form("add_participant"):
        new_name = st.text_input("Nombre del participante")
        new_shares = st.number_input("Cantidad de personas / cupos", min_value=1, value=1, step=1)
        add_btn = st.form_submit_button("Agregar Participante")
        if add_btn and new_name:
            if new_name not in participant_names:
                st.session_state['participants'].append({"name": new_name, "shares": int(new_shares)})
                st.success(f"¡Participante {new_name} agregado!")
                st.rerun()
            else:
                st.error("El participante ya existe.")
                
    st.write("Participantes actuales:")
    for p in st.session_state['participants']:
        col1, col2 = st.columns([3, 1])
        col1.write(f"👤 **{p['name']}** (Cupos: {p['shares']})")
        if col2.button("Eliminar", key=f"del_p_list_{p['name']}"):
            st.session_state['participants'] = [x for x in st.session_state['participants'] if x['name'] != p['name']]
            st.rerun()
