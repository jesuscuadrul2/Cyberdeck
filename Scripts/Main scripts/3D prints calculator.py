```
import streamlit as st
import pymysql
import pandas as pd
import re

# ==========================================
# 1. CONFIGURACIÓN VISUAL Y ESTADO (ThreeDC)
# ==========================================
st.set_page_config(page_title="ThreeDC ERP", page_icon="⚡", layout="wide")
st.title("⚡ ThreeDC - Sistema Integrado de Manufactura v4.5")

if 'num_materiales' not in st.session_state: st.session_state['num_materiales'] = 1
if 'num_materiales_rd' not in st.session_state: st.session_state['num_materiales_rd'] = 1
if 'num_proyectos_lote' not in st.session_state: st.session_state['num_proyectos_lote'] = 2
if 'num_proyectos_lote_rd' not in st.session_state: st.session_state['num_proyectos_lote_rd'] = 2
if 'ui_key' not in st.session_state: st.session_state['ui_key'] = 0

def reset_cotizador():
    st.session_state['num_materiales'] = 1
    st.session_state['num_materiales_rd'] = 1
    st.session_state['num_proyectos_lote'] = 2
    st.session_state['num_proyectos_lote_rd'] = 2
    st.session_state['ui_key'] += 1

opciones_extras = {
    "Ninguno ($0.00)": 0.0,
    "Nivel 1: Básico (1-4 insertos/imanes/NFC) ($25.00)": 25.0,
    "Nivel 2: Intermedio (5-10 insertos, tornillos) ($50.00)": 50.0,
    "Nivel 3: Avanzado (Ensambles complejos) ($120.00)": 120.0
}

# ⚡ CONSTANTES DE TALLER
COSTO_KWH = 0.0  
CONSUMO_IMPRESORA = 0.15 
AMORTIZACION_HORA = 5.00  
MANO_OBRA_FIJA = 40.00  
TIEMPO_CALIBRACION_MIN = 10 

# ==========================================
# 2. CONEXIÓN A BASE DE DATOS
# ==========================================
def get_connection():
    return pymysql.connect(
        host="pragmata_db", user="diana_bot", password="(JC2)^-1", 
        database="pragmata_erp", cursorclass=pymysql.cursors.DictCursor
    )

def get_inventory():
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Catalogo_Filamentos")
            datos = cursor.fetchall()
        conn.close()
        return datos
    except: return []

inventario = get_inventory()
filamentos_dict = {f"{f['Marca']} {f['Material']} {f['Color']}": f for f in inventario}

# ==========================================
# 3. BARRA LATERAL: BÓVEDA, AUDITORÍA Y GASTOS
# ==========================================
with st.sidebar:
    st.markdown("### 🏦 Bóveda ThreeDC")
    if st.button("💳 Consultar Flujo de Caja", use_container_width=True):
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN Tipo = 'Ingreso' THEN Monto ELSE 0 END), 0) AS ing,
                        COALESCE(SUM(CASE WHEN Tipo = 'Gasto' THEN Monto ELSE 0 END), 0) AS gst,
                        (COALESCE(SUM(CASE WHEN Tipo = 'Ingreso' THEN Monto ELSE 0 END), 0) - COALESCE(SUM(CASE WHEN Tipo = 'Gasto' THEN Monto ELSE 0 END), 0)) AS neto
                    FROM Finanzas_Flujo
                """)
                f = cursor.fetchone()
            conn.close()
            st.metric(label="Efectivo Libre en Caja", value=f"${float(f['neto']):,.2f} MXN", delta=f"-${float(f['gst']):,.2f} en Egresos", delta_color="normal")
            st.caption(f"📈 **Ingresos Brutos:** ${float(f['ing']):,.2f} MXN")
        except Exception as e: st.error(f"Error BD: {e}")
            
    if st.button("🌱 Ver Costo Neto de Producción", use_container_width=True):
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""SELECT SUM((r.Gramos_Usados / 1000) * c.Precio_Rollo) AS costo_neto 
                                  FROM Registro_Impresiones r JOIN Catalogo_Filamentos c ON r.ID_Filamento = c.ID_Filamento 
                                  WHERE r.Estado_Trabajo = 'Impreso'""")
                res_neto = cursor.fetchone()
                costo_neto = float(res_neto['costo_neto'] or 0.0)
            conn.close()
            st.metric(label="Inversión en Silicio y Plástico", value=f"${costo_neto:,.2f} MXN")
        except Exception as e: st.error(f"Error BD: {e}")

    st.markdown("---")
    
    with st.expander("💸 Capturar Egreso / Alta Insumos"):
        tipo_movimiento = st.radio("Tipo de Egreso:", ["Gasto General", "Alta de Filamento Nuevo"], key=f"rad_tipo_{st.session_state['ui_key']}")
        
        if tipo_movimiento == "Gasto General":
            g_cat = st.selectbox("Categoría:", ["Insumos", "Herramienta", "Mantenimiento / Refacciones", "Logística / Envíos", "Servicios (Luz/Internet)", "Otros"], key=f"gcat_{st.session_state['ui_key']}")
            g_desc = st.text_input("Descripción:", placeholder="Ej. 5pcs Pegamento Epóxico", key=f"gdesc_{st.session_state['ui_key']}")
            g_monto = st.number_input("Costo Pagado ($ MXN):", min_value=0.5, value=299.0, step=10.0, key=f"gmonto_{st.session_state['ui_key']}")
            
            if st.button("📥 Descontar de la Bóveda", type="primary", use_container_width=True):
                if g_desc.strip():
                    try:
                        conn = get_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("INSERT INTO Finanzas_Flujo (Tipo, Monto, Categoria, Descripcion) VALUES ('Gasto', %s, %s, %s)", (g_monto, g_cat, g_desc.strip()))
                        conn.commit(); conn.close()
                        st.success(f"¡Gasto de ${g_monto} registrado en {g_cat}!")
                        reset_cotizador(); st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
                else: st.warning("Escríbele una descripción al gasto.")
                
        else:
            st.markdown("#### 🧵 Nuevo Rollo de Filamento")
            c_f1, c_f2 = st.columns(2)
            with c_f1: f_marca = st.text_input("Marca:", placeholder="Ej. Sunlu", key=f"fmar_{st.session_state['ui_key']}")
            with c_f2: f_mat = st.text_input("Material:", placeholder="Ej. PLA+", key=f"fmat_{st.session_state['ui_key']}")
            
            c_f3, c_f4 = st.columns(2)
            with c_f3: f_col = st.text_input("Color:", placeholder="Ej. Blanco", key=f"fcol_{st.session_state['ui_key']}")
            with c_f4: f_peso = st.number_input("Stock Inicial (g):", min_value=100.0, value=1000.0, step=100.0, key=f"fpeso_{st.session_state['ui_key']}")
            
            f_precio = st.number_input("Costo del Rollo ($ MXN):", min_value=10.0, value=300.0, step=10.0, key=f"fpre_{st.session_state['ui_key']}")

            if st.button("📥 Registrar Filamento y Descontar", type="primary", use_container_width=True):
                if f_marca and f_mat and f_col:
                    try:
                        conn = get_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("INSERT INTO Catalogo_Filamentos (Marca, Material, Color, Precio_Rollo, Stock_Actual_Gramos, Stock_Apartado_Gramos) VALUES (%s, %s, %s, %s, %s, 0)", 
                                           (f_marca.strip(), f_mat.strip(), f_col.strip(), f_precio, f_peso))
                            desc_gasto = f"Compra: {f_marca.strip()} {f_mat.strip()} {f_col.strip()}"
                            cursor.execute("INSERT INTO Finanzas_Flujo (Tipo, Monto, Categoria, Descripcion) VALUES ('Gasto', %s, 'Filamento', %s)", 
                                           (f_precio, desc_gasto))
                        conn.commit(); conn.close()
                        st.success(f"¡Filamento {f_mat} dado de alta exitosamente!")
                        reset_cotizador(); st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
                else: st.warning("Por favor llena la Marca, Material y Color.")

    with st.expander("⚖️ Auditoría Física (Calibrar Carrete)"):
        carrete_target = st.selectbox("Seleccionar Carrete:", list(filamentos_dict.keys()), key=f"caudit_{st.session_state['ui_key']}")
        peso_bascula = st.number_input("Gramos reales sobrantes:", min_value=0.0, max_value=3000.0, value=500.0, step=10.0, key=f"cpeso_{st.session_state['ui_key']}")
        if st.button("💾 Aplicar Verdad Física", type="secondary", use_container_width=True):
            try:
                id_fil_audit = filamentos_dict[carrete_target]['ID_Filamento']
                conn = get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE Catalogo_Filamentos SET Stock_Actual_Gramos = %s WHERE ID_Filamento = %s", (peso_bascula, id_fil_audit))
                conn.commit(); conn.close(); st.success(f"¡Calibrado a {peso_bascula}g!"); st.rerun()
            except Exception as e: st.error(e)

    st.markdown("---")
    st.caption("ThreeDC ERP v4.5 | Finanzas Avanzadas")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Cotizador Cliente", "📦 Lotes Cliente", "🖲️ Proyectos (R&D Neto)", "📋 Gestor de Cola", "📈 Reportes Financieros"])
ukey = st.session_state['ui_key']

# ==========================================
# PESTAÑA 1: COTIZADOR CLIENTE (1 a 1)
# ==========================================
with tab1:
    nombre_proyecto = st.text_input("Nombre del Cliente / Proyecto:", key=f"nombre_{ukey}")
    materiales_seleccionados = []
    
    for i in range(st.session_state['num_materiales']):
        c_mat1, c_mat2, c_mat3, c_mat4 = st.columns([3, 2, 1, 1])
        with c_mat1: fil = st.selectbox(f"Filamento {i+1}:", options=list(filamentos_dict.keys()), key=f"c_fil_{i}_{ukey}")
        with c_mat2: g = st.number_input(f"Gramos {i+1}:", min_value=1.0, value=50.0, key=f"c_g_{i}_{ukey}")
        with c_mat3: h = st.number_input(f"Hrs {i+1}:", min_value=0, value=1, step=1, key=f"c_h_{i}_{ukey}")
        with c_mat4: m = st.number_input(f"Min {i+1}:", min_value=0, max_value=59, value=0, step=1, key=f"c_m_{i}_{ukey}")
        materiales_seleccionados.append({"fil_obj": filamentos_dict[fil], "g": g, "h": h, "m": m})
        
    c_btn1, c_btn2 = st.columns([1, 4])
    with c_btn1:
        if st.button("➕ Agregar filamento", key=f"add_c_{ukey}"):
            st.session_state['num_materiales'] += 1; st.rerun()
    with c_btn2:
        if st.session_state['num_materiales'] > 1:
            if st.button("➖ Quitar filamento", key=f"rem_c_{ukey}"):
                st.session_state['num_materiales'] -= 1; st.rerun()

    total_h = sum(mat['h'] for mat in materiales_seleccionados)
    total_m_base = sum(mat['m'] for mat in materiales_seleccionados)
    
    minutos_totales_bd = int((total_h * 60) + total_m_base) + TIEMPO_CALIBRACION_MIN
    horas_req = minutos_totales_bd / 60.0

    st.markdown("---")
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1: extra_cost = opciones_extras[st.selectbox("Insumos Extra:", list(opciones_extras.keys()), key=f"cx_{ukey}")]
    with col_v2: merma = st.slider("Margen de Merma (%)", 0, 100, 10, key=f"cm_{ukey}")
    with col_v3: pct_mantenimiento = st.slider("Fondo Reserva Máquina (%)", 0, 30, 10, step=5, key=f"pmaint_{ukey}")

    st.markdown("### 💼 Costos Operativos, Logística y Diseño")
    col_op1, col_op2, col_op3, col_op4 = st.columns(4)
    with col_op1: horas_diseno = st.number_input("Horas Diseño (CAD):", min_value=0.0, step=0.5, value=0.0, key=f"cad_{ukey}")
    with col_op2: tarifa_diseno = st.number_input("Tarifa Diseño/hr ($):", min_value=0.0, step=50.0, value=150.0, key=f"tcad_{ukey}")
    with col_op3: costo_envio = st.number_input("Costo de Envío ($):", min_value=0.0, step=10.0, value=0.0, key=f"env_{ukey}")
    with col_op4: porcentaje_empleado = st.number_input("Comisión (%):", min_value=0, max_value=100, value=0, key=f"emp_{ukey}")

    costo_mat = sum((mat["g"]/1000)*float(mat["fil_obj"]['Precio_Rollo']) for mat in materiales_seleccionados)
    costo_puro_fab = (costo_mat * (1 + (merma/100))) + (horas_req * AMORTIZACION_HORA)
    
    subtotal_operativo = costo_puro_fab + extra_cost + MANO_OBRA_FIJA + costo_envio + (horas_diseno * tarifa_diseno)
    costo_base = subtotal_operativo * (1 + (pct_mantenimiento / 100))

    p_amigo = costo_base * 1.3
    p_reg = costo_base * 2.5
    p_urg = costo_base * 4.0

    st.markdown("### 💰 Resumen Financiero")
    c_net1, c_net2 = st.columns(2)
    c_net1.metric("🔬 Costo Puro (Material + Tiempo)", f"${costo_puro_fab:.2f}")
    c_net2.metric("🛠️ Costo Operativo Total (+ Mano de Obra)", f"${costo_base:.2f}")
    
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("🫂 Precio Amigo", f"${p_amigo:.2f}")
    c2.metric("🏭 Precio Regular", f"${p_reg:.2f}")
    c3.metric("🛑 Precio NLQHPSLPLI", f"${p_urg:.2f}")

    st.markdown("#### 🛒 Determinar Precio Final")
    tipo_precio = st.radio("Selecciona la tarifa a aplicar:", ["Regular", "Amigo", "Urgente", "Acordado (Manual)"], horizontal=True, key=f"tp_{ukey}")
    
    precio_acordado = p_reg
    if tipo_precio == "Acordado (Manual)":
        precio_acordado = st.number_input("Ingresa el precio final acordado con el cliente ($):", min_value=0.0, value=float(round(p_reg)), key=f"pa_{ukey}")

    val_cobro_actual = precio_acordado if tipo_precio == "Acordado (Manual)" else (p_amigo if tipo_precio == "Amigo" else (p_urg if tipo_precio == "Urgente" else p_reg))
    monto_mantenimiento_calc = val_cobro_actual * (pct_mantenimiento / 100)
    st.caption(f"🔧 **El cliente pagará un extra oculto de:** ${monto_mantenimiento_calc:.2f} MXN para refacciones de la máquina.")

    if st.button("📥 Enviar a Cola Cliente", type="primary"):
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                for idx, mat in enumerate(materiales_seleccionados):
                    p_cobro_bd = val_cobro_actual if idx == 0 else 0.0
                    min_bd = minutos_totales_bd if idx == 0 else 0
                    etiq = f"{nombre_proyecto} (Mat {idx+1}/{len(materiales_seleccionados)})" if len(materiales_seleccionados)>1 else nombre_proyecto
                    cursor.execute("""INSERT INTO Registro_Impresiones (ID_Filamento, Gramos_Usados, Minutos_Impresion, Nombre_Cliente, Estado_Trabajo, Precio_Cobrado_MXN) 
                                      VALUES (%s, %s, %s, %s, 'En Cola', %s)""", 
                                      (mat["fil_obj"]['ID_Filamento'], mat['g'], min_bd, etiq, p_cobro_bd))
                    cursor.execute("UPDATE Catalogo_Filamentos SET Stock_Apartado_Gramos = Stock_Apartado_Gramos + %s WHERE ID_Filamento = %s", (mat['g'], mat["fil_obj"]['ID_Filamento']))
            conn.commit(); conn.close(); reset_cotizador(); st.rerun()
        except Exception as e: st.error(e)

# ==========================================
# PESTAÑA 2 y 3: LOTES Y R&D
# ==========================================
with tab2:
    st.info("Distribución de costos comerciales para piezas en una sola placa.")
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1: fil_l = st.selectbox("Filamento Placa:", list(filamentos_dict.keys()), key=f"l_fil_{ukey}")
    with col_l2: h_l = st.number_input("Horas Totales:", 0, value=2, key=f"l_h_{ukey}")
    with col_l3: m_l = st.number_input("Minutos Totales:", 0, 59, 30, key=f"l_m_{ukey}")

    minutos_totales_lote = (h_l * 60) + m_l + TIEMPO_CALIBRACION_MIN
    horas_req_l = minutos_totales_lote / 60.0
    costo_op_placa = (horas_req_l * AMORTIZACION_HORA) + MANO_OBRA_FIJA
    proyectos_lote = []
    g_totales = 0.0
    
    for i in range(st.session_state['num_proyectos_lote']):
        c1, c2 = st.columns([3, 1])
        with c1: np = st.text_input(f"Proyecto {i+1}:", key=f"l_n_{i}_{ukey}")
        with c2: gp = st.number_input(f"Gramos {i+1}:", min_value=1.0, value=20.0, key=f"l_g_{i}_{ukey}")
        proyectos_lote.append({"nom": np, "g": gp})
        g_totales += gp

    if st.button("➕ Proyecto a Lote", key=f"add_l_{ukey}"): st.session_state['num_proyectos_lote'] += 1; st.rerun()

    if fil_l in filamentos_dict:
        fil_d = filamentos_dict[fil_l]
        c_base_placa = ((g_totales/1000) * float(fil_d['Precio_Rollo'])) + costo_op_placa

        datos_prorr = []
        st.markdown("#### ⚖️ Desglose Prorrateado y Ajuste de Precio")
        for i, p in enumerate(proyectos_lote):
            if g_totales > 0 and p["nom"]:
                factor = p["g"] / g_totales
                sugerido = (c_base_placa * factor) * 2.5
                c_p1, c_p2 = st.columns([2, 1])
                with c_p1: st.write(f"**{p['nom']}**: Absorbe {factor*100:.1f}% de placa. (Sug: ${sugerido:.2f})")
                with c_p2: precio_final_lote = st.number_input("Cobrar ($):", min_value=0.0, value=float(round(sugerido)), key=f"lp_{i}_{ukey}")
                datos_prorr.append({"nom": p["nom"], "g": p["g"], "min": int(minutos_totales_lote * factor), "precio": precio_final_lote})

        if st.button("📥 Enviar Lote Comercial", type="primary"):
            try:
                conn = get_connection()
                with conn.cursor() as cursor:
                    for d in datos_prorr:
                        cursor.execute("""INSERT INTO Registro_Impresiones (ID_Filamento, Gramos_Usados, Minutos_Impresion, Nombre_Cliente, Estado_Trabajo, Precio_Cobrado_MXN) 
                                          VALUES (%s, %s, %s, %s, 'En Cola', %s)""", 
                                          (fil_d['ID_Filamento'], d['g'], d['min'], d['nom'], d['precio']))
                        cursor.execute("UPDATE Catalogo_Filamentos SET Stock_Apartado_Gramos = Stock_Apartado_Gramos + %s WHERE ID_Filamento = %s", (d['g'], fil_d['ID_Filamento']))
                conn.commit(); conn.close(); reset_cotizador(); st.rerun()
            except Exception as e: st.error(e)

with tab3:
    st.markdown("### 🖲️ Laboratorio R&D (Costo de Material Puro)")
    proyecto_target = st.text_input("Proyecto I+D Destino (Ej. Cyberdeck, VTOL Drone, SCADA):", value="Cyberdeck", key=f"p_target_{ukey}").strip()
    
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COALESCE(SUM(Monto), 0) AS total_rd FROM Finanzas_Cyberdeck")
            total_cyber = float(cursor.fetchone()['total_rd'])
            cursor.execute("SELECT COALESCE(SUM(Monto), 0) AS total_alt FROM Finanzas_Flujo WHERE Categoria LIKE 'R&D - %' OR Tipo = 'Inversion_RD'")
            total_otros = float(cursor.fetchone()['total_alt'])
        conn.close()
    except: total_cyber, total_otros = 0.0, 0.0
    
    c_m1, c_m2 = st.columns(2)
    c_m1.metric("Inversión en Cyberdeck (Baby Jarvis)", f"${total_cyber:,.2f} MXN")
    c_m2.metric("Inversión en Otros Proyectos R&D", f"${total_otros:,.2f} MXN")
    st.markdown("---")

    modo_rd = st.radio("Estrategia de Impresión R&D:", ["Prototipo Individual (1 a 1)", "Lote de Prototipos en Placa"], horizontal=True, key=f"rad_rd_{ukey}")

    if modo_rd == "Prototipo Individual (1 a 1)":
        nom_rd = st.text_input("Módulo a Imprimir:", key=f"rd_nom_{ukey}")
        mat_rd = []
        for i in range(st.session_state['num_materiales_rd']):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            with c1: f_rd = st.selectbox(f"Filamento {i+1}:", list(filamentos_dict.keys()), key=f"r_f_{i}_{ukey}")
            with c2: g_rd = st.number_input(f"Gramos {i+1}:", min_value=1.0, value=50.0, key=f"r_g_{i}_{ukey}")
            with c3: h_rd = st.number_input(f"Hrs {i+1}:", min_value=0, value=1, step=1, key=f"r_h_{i}_{ukey}")
            with c4: m_rd = st.number_input(f"Min {i+1}:", min_value=0, max_value=59, value=0, step=1, key=f"r_m_{i}_{ukey}")
            mat_rd.append({"fil_obj": filamentos_dict[f_rd], "g": g_rd, "h": h_rd, "m": m_rd})

        cr_btn1, cr_btn2 = st.columns([1, 4])
        with cr_btn1:
            if st.button("➕ Material R&D", key=f"add_r_{ukey}"): st.session_state['num_materiales_rd'] += 1; st.rerun()
        with cr_btn2:
            if st.session_state['num_materiales_rd'] > 1:
                if st.button("➖ Quitar material", key=f"rem_r_{ukey}"): st.session_state['num_materiales_rd'] -= 1; st.rerun()

        costo_neto_rd = 0.0
        for mat in mat_rd:
            id_f = mat["fil_obj"]['ID_Filamento']
            p_real = float(mat["fil_obj"]['Precio_Rollo'])
            try:
                conn = get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT Monto FROM Finanzas_Flujo WHERE Categoria = 'Filamento' AND ID_Transaccion = (SELECT MAX(ID_Transaccion) FROM Finanzas_Flujo WHERE Descripcion LIKE %s)", (f"%{mat['fil_obj']['Marca']}%",))
                    res = cursor.fetchone()
                    if res and res['Monto']: p_real = float(res['Monto'])
                conn.close()
            except: pass
            costo_neto_rd += (mat["g"] / 1000) * p_real
            
        total_min_rd = sum((mat['h'] * 60) + mat['m'] for mat in mat_rd) + TIEMPO_CALIBRACION_MIN
        st.metric(f"🔬 Costo Neto (Hacia {proyecto_target})", f"${costo_neto_rd:.2f} MXN", f"Vuelo Automático: {total_min_rd} min")

        if st.button("📥 Enviar Prototipo a Cola", type="secondary"):
            try:
                conn = get_connection()
                with conn.cursor() as cursor:
                    for idx, mat in enumerate(mat_rd):
                        c_bd = costo_neto_rd if idx == 0 else 0.0
                        min_bd = total_min_rd if idx == 0 else 0 
                        etiq = f"[R&D][{proyecto_target}] {nom_rd} (Mat {idx+1}/{len(mat_rd)})" if len(mat_rd)>1 else f"[R&D][{proyecto_target}] {nom_rd}"
                        cursor.execute("""INSERT INTO Registro_Impresiones (ID_Filamento, Gramos_Usados, Minutos_Impresion, Nombre_Cliente, Estado_Trabajo, Precio_Cobrado_MXN) 
                                          VALUES (%s, %s, %s, %s, 'En Cola', %s)""", 
                                          (mat["fil_obj"]['ID_Filamento'], mat['g'], min_bd, etiq, c_bd))
                        cursor.execute("UPDATE Catalogo_Filamentos SET Stock_Apartado_Gramos = Stock_Apartado_Gramos + %s WHERE ID_Filamento = %s", (mat['g'], mat["fil_obj"]['ID_Filamento']))
                conn.commit(); conn.close(); reset_cotizador(); st.rerun()
            except Exception as e: st.error(e)

# ==========================================
# PESTAÑA 4: GESTOR DE COLA Y RE-COTIZADOR
# ==========================================
with tab4:
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT r.ID_Impresion, r.Nombre_Cliente, c.Material, c.Color, c.Marca, r.Gramos_Usados, r.Precio_Cobrado_MXN, r.Estado_Trabajo, r.ID_Filamento, r.Minutos_Impresion FROM Registro_Impresiones r JOIN Catalogo_Filamentos c ON r.ID_Filamento = c.ID_Filamento WHERE r.Estado_Trabajo = 'En Cola'")
            cola = cursor.fetchall()
        conn.close()
    except: cola = []

    if not cola: 
        st.info("Agenda libre. Diana está en espera.")
    else:
        proyectos_agrupados = {}
        for row in cola:
            nb = re.sub(r' \(Mat \d+(?:/\d+)?\)$', '', row['Nombre_Cliente'])
            if nb not in proyectos_agrupados: proyectos_agrupados[nb] = {'IDs': [], 'Desc': [], 'G': 0.0, 'P': 0.0, 'Min': 0, 'Items': []}
            proyectos_agrupados[nb]['IDs'].append(row['ID_Impresion'])
            proyectos_agrupados[nb]['Desc'].append(f"{row['Material']} {row['Color']} ({row['Gramos_Usados']}g)")
            proyectos_agrupados[nb]['G'] += float(row['Gramos_Usados'])
            proyectos_agrupados[nb]['P'] += float(row['Precio_Cobrado_MXN'])
            proyectos_agrupados[nb]['Min'] += int(row['Minutos_Impresion'])
            proyectos_agrupados[nb]['Items'].append(row)
        
        datos_tabla = [{"Proyecto": n, "Materiales": " + ".join(d['Desc']), "Gramos": f"{d['G']:.1f}g", "Minutos": f"{d['Min']}m", "Total": f"${d['P']:.2f}"} for n, d in proyectos_agrupados.items()]
        st.dataframe(pd.DataFrame(datos_tabla), use_container_width=True)
        
        st.markdown("---")
        st.markdown("### ⚙️ Gestión de Pedido")
        p_sel = st.selectbox("Selecciona un proyecto para procesar o editar:", list(proyectos_agrupados.keys()))
        d_sel = proyectos_agrupados[p_sel]

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("❌ Cancelar Proyecto", use_container_width=True):
                try:
                    conn = get_connection(); cursor = conn.cursor()
                    for p_id in d_sel['IDs']:
                        cursor.execute("SELECT ID_Filamento, Gramos_Usados FROM Registro_Impresiones WHERE ID_Impresion = %s", (p_id,))
                        res = cursor.fetchone()
                        cursor.execute("UPDATE Registro_Impresiones SET Estado_Trabajo = 'Cancelado' WHERE ID_Impresion = %s", (p_id,))
                        cursor.execute("UPDATE Catalogo_Filamentos SET Stock_Apartado_Gramos = Stock_Apartado_Gramos - %s WHERE ID_Filamento = %s", (res['Gramos_Usados'], res['ID_Filamento']))
                    conn.commit(); conn.close(); st.rerun()
                except Exception as e: st.error(e)

        with col_b:
             pct_cobro_maint = st.number_input("Retención a Bóveda Refacciones al Cobrar (%):", min_value=0, max_value=30, value=10, key=f"ret_{p_sel}")
             if st.button("✅ ¡Impreso! (Cobrar y descontar stock)", type="primary", use_container_width=True):
                try:
                    conn = get_connection(); cursor = conn.cursor()
                    for p_id in d_sel['IDs']:
                        cursor.execute("SELECT ID_Filamento, Gramos_Usados, Precio_Cobrado_MXN, Nombre_Cliente FROM Registro_Impresiones WHERE ID_Impresion = %s", (p_id,))
                        p = cursor.fetchone()
                        cursor.execute("UPDATE Registro_Impresiones SET Estado_Trabajo = 'Impreso' WHERE ID_Impresion = %s", (p_id,))
                        cursor.execute("UPDATE Catalogo_Filamentos SET Stock_Actual_Gramos = Stock_Actual_Gramos - %s, Stock_Apartado_Gramos = Stock_Apartado_Gramos - %s WHERE ID_Filamento = %s", (p['Gramos_Usados'], p['Gramos_Usados'], p['ID_Filamento']))
                        
                        monto_transaccion = float(p['Precio_Cobrado_MXN'])
                        if monto_transaccion > 0:
                            match_rd = re.match(r'^\[R&D\]\[(.*?)\]\s*(.*)', p['Nombre_Cliente'])
                            if match_rd:
                                proy_name = match_rd.group(1)
                                piez_name = match_rd.group(2)
                                if proy_name.lower() == "cyberdeck":
                                    cursor.execute("INSERT INTO Finanzas_Cyberdeck (Monto, Categoria, Descripcion) VALUES (%s, 'Prototipo', %s)", (monto_transaccion, piez_name))
                                else:
                                    cursor.execute("INSERT INTO Finanzas_Flujo (Tipo, Monto, Categoria, Descripcion) VALUES ('Inversion_RD', %s, %s, %s)", 
                                                   (monto_transaccion, f"R&D - {proy_name}", piez_name))
                            else:
                                retencion_maint = monto_transaccion * (pct_cobro_maint / 100)
                                neto_caja = monto_transaccion - retencion_maint
                                
                                cursor.execute("INSERT INTO Finanzas_Flujo (Tipo, Monto, Categoria, Descripcion) VALUES ('Ingreso', %s, 'Impresión Comercial', %s)", (neto_caja, p['Nombre_Cliente']))
                                if retencion_maint > 0:
                                    cursor.execute("INSERT INTO Finanzas_Flujo (Tipo, Monto, Categoria, Descripcion) VALUES ('Ingreso', %s, 'Fondo Mantenimiento', %s)", (retencion_maint, f"Reserva Diana: {p['Nombre_Cliente']}"))
                                
                    conn.commit(); conn.close(); st.rerun()
                except Exception as e: st.error(e)

        with st.expander("🛠️ Re-Cotizador Completo (Modificar Pedido)"):
            st.write(f"**Reestructurando orden:** {p_sel}")
            edit_mats = []
            for idx, item in enumerate(d_sel['Items']):
                c1_e, c2_e = st.columns([3, 2])
                fil_str_actual = f"{item['Marca']} {item['Material']} {item['Color']}"
                opciones_cat = list(filamentos_dict.keys())
                index_defecto = opciones_cat.index(fil_str_actual) if fil_str_actual in opciones_cat else 0
                with c1_e: e_fil = st.selectbox(f"Filamento {idx+1}:", opciones_cat, index=index_defecto, key=f"ef_{item['ID_Impresion']}")
                with c2_e: e_g = st.number_input("Nuevos Gramos:", min_value=1.0, value=float(item['Gramos_Usados']), key=f"eg_{item['ID_Impresion']}")
                edit_mats.append({"id_imp": item['ID_Impresion'], "id_fil_viejo": item['ID_Filamento'], "g_viejo": float(item['Gramos_Usados']), "fil_obj": filamentos_dict[e_fil], "g": e_g})

            minutos_bd_sin_calibracion = sum(int(item['Minutos_Impresion']) for item in d_sel['Items']) - TIEMPO_CALIBRACION_MIN
            if minutos_bd_sin_calibracion < 0: minutos_bd_sin_calibracion = 0
            
            col_t1, col_t2 = st.columns(2)
            with col_t1: e_h_tot = st.number_input("Horas Puras de Slicer:", min_value=0, value=minutos_bd_sin_calibracion // 60, step=1, key=f"ehtot_{p_sel}")
            with col_t2: e_m_tot = st.number_input("Minutos Puros de Slicer:", min_value=0, max_value=59, value=minutos_bd_sin_calibracion % 60, step=1, key=f"emtot_{p_sel}")
            
            minutos_totales_recalculados = (e_h_tot * 60) + e_m_tot + TIEMPO_CALIBRACION_MIN
            horas_req_e = minutos_totales_recalculados / 60.0

            st.markdown("---")
            col1_e, col2_e, col3_e = st.columns(3)
            with col1_e: ex_c_e = opciones_extras[st.selectbox("Insumos Extra:", list(opciones_extras.keys()), key=f"ecx_{p_sel}")]
            with col2_e: mer_e = st.slider("Nuevo Margen de Merma (%)", 0, 100, 10, key=f"ecm_{p_sel}")
            with col3_e: maint_e = st.slider("Nuevo Fondo Reserva (%)", 0, 30, 10, key=f"ecmaint_{p_sel}")

            c_o1, c_o2, c_o3, c_o4 = st.columns(4)
            with c_o1: h_cad_e = st.number_input("Horas Diseño (CAD):", min_value=0.0, step=0.5, value=0.0, key=f"ecad_{p_sel}")
            with c_o2: t_cad_e = st.number_input("Tarifa Diseño/hr ($):", min_value=0.0, step=50.0, value=150.0, key=f"etcad_{p_sel}")
            with c_o3: c_env_e = st.number_input("Costo de Envío ($):", min_value=0.0, step=10.0, value=0.0, key=f"eenv_{p_sel}")
            with c_o4: p_emp_e = st.number_input("Comisión (%):", min_value=0, max_value=100, value=0, key=f"eemp_{p_sel}")

            costo_mat_e = sum((m["g"]/1000)*float(m["fil_obj"]['Precio_Rollo']) for m in edit_mats)
            costo_puro_fab_e = (costo_mat_e * (1 + (mer_e/100))) + (horas_req_e * AMORTIZACION_HORA)
            
            subtotal_e = costo_puro_fab_e + ex_c_e + MANO_OBRA_FIJA + c_env_e + (h_cad_e * t_cad_e)
            costo_base_e = subtotal_e * (1 + (maint_e/100))
            
            p_amigo_e = costo_base_e * 1.3
            p_reg_e = costo_base_e * 2.5
            p_urg_e = costo_base_e * 4.0

            st.markdown("### 💰 Nueva Cotización Generada")
            cn1_e, cn2_e = st.columns(2)
            cn1_e.metric("🔬 Costo Puro (Material + Tiempo)", f"${costo_puro_fab_e:.2f}")
            cn2_e.metric("🛠️ Costo Operativo Total (+ Mano de Obra)", f"${costo_base_e:.2f}")
            
            st.markdown("---")
            c1e, c2e, c3e = st.columns(3)
            c1e.metric("🫂 Precio Amigo", f"${p_amigo_e:.2f}")
            c2e.metric("🏭 Precio Regular", f"${p_reg_e:.2f}")
            c3e.metric("🛑 Precio NLQHPSLPLI", f"${p_urg_e:.2f}")

            precio_a_guardar = st.radio("Selecciona qué precio aplicar a la base de datos:", 
                                       ["Aplicar Precio Regular Nuevo", "Aplicar Precio Amigo", "Aplicar Precio Urgente", "Mantener precio original pactado", "Precio Acordado (Manual)"], key=f"paguar_{p_sel}")

            precio_manual_e = p_reg_e
            if "Manual" in precio_a_guardar:
                precio_manual_e = st.number_input("Ingresa el nuevo precio acordado ($):", min_value=0.0, value=float(round(p_reg_e)), key=f"pme_{p_sel}")

            if st.button("💾 Procesar y Sobreescribir Orden", type="primary"):
                val_cobro = p_reg_e
                if "Amigo" in precio_a_guardar: val_cobro = p_amigo_e
                elif "Urgente" in precio_a_guardar: val_cobro = p_urg_e
                elif "original" in precio_a_guardar: val_cobro = d_sel['P']
                elif "Manual" in precio_a_guardar: val_cobro = precio_manual_e

                try:
                    conn = get_connection()
                    with conn.cursor() as cursor:
                        for idx, m in enumerate(edit_mats):
                            cursor.execute("UPDATE Catalogo_Filamentos SET Stock_Apartado_Gramos = Stock_Apartado_Gramos - %s WHERE ID_Filamento = %s", (m['g_viejo'], m['id_fil_viejo']))
                            cursor.execute("UPDATE Catalogo_Filamentos SET Stock_Apartado_Gramos = Stock_Apartado_Gramos + %s WHERE ID_Filamento = %s", (m['g'], m['fil_obj']['ID_Filamento']))
                            p_cobro_bd = val_cobro if idx == 0 else 0.0
                            min_bd = minutos_totales_recalculados if idx == 0 else 0
                            cursor.execute("""UPDATE Registro_Impresiones SET ID_Filamento = %s, Gramos_Usados = %s, Minutos_Impresion = %s, Precio_Cobrado_MXN = %s WHERE ID_Impresion = %s""", 
                                          (m['fil_obj']['ID_Filamento'], m['g'], min_bd, p_cobro_bd, m['id_imp']))
                    conn.commit(); conn.close(); reset_cotizador(); st.rerun()
                except Exception as e: st.error(f"Error BD: {e}")

# ==========================================
# PESTAÑA 5: DASHBOARD FINANCIERO (NUEVO)
# ==========================================
with tab5:
    st.markdown("### 📈 Análisis de Inteligencia de Negocios")
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 🛡️ Extraemos los datos con el cursor nativo para evitar que Pandas se pelee con el DictCursor
            cursor.execute("SELECT Fecha, Tipo, Monto, Categoria, Descripcion FROM Finanzas_Flujo")
            datos_finanzas = cursor.fetchall()
        conn.close()

        if datos_finanzas:
            # Creamos el DataFrame directamente desde el diccionario de la base de datos
            df_fin = pd.DataFrame(datos_finanzas)
            
            # Convertimos explícitamente a números (esto maneja el formato Decimal nativo de MySQL)
            df_fin['Monto'] = pd.to_numeric(df_fin['Monto'], errors='coerce').fillna(0.0)
            
            # Clasificación rápida
            df_ingresos = df_fin[df_fin['Tipo'] == 'Ingreso']
            df_gastos = df_fin[df_fin['Tipo'] == 'Gasto']
            df_rd = df_fin[df_fin['Tipo'] == 'Inversion_RD']

            col_met1, col_met2, col_met3 = st.columns(3)
            col_met1.metric("💵 Ingresos Brutos Totales", f"${df_ingresos['Monto'].sum():,.2f}")
            col_met2.metric("💸 Gastos Operativos Acumulados", f"${df_gastos['Monto'].sum():,.2f}")
            col_met3.metric("🔬 Capital Hundido en R&D", f"${df_rd['Monto'].sum():,.2f}")

            st.markdown("---")
            st.markdown("#### 📊 Dónde se está yendo el dinero (Salidas de Caja)")
            
            # Juntamos los gastos y el R&D para ver las salidas de dinero
            df_salidas = pd.concat([df_gastos, df_rd])
            
            if not df_salidas.empty and df_salidas['Monto'].sum() > 0:
                # Limpiar categorías de R&D para mejor visualización
                df_salidas['Categoria_Plot'] = df_salidas['Categoria'].apply(lambda x: "Inversión R&D" if str(x).startswith("R&D") else x)
                
                # Agrupar por la categoría limpia
                resumen_cat = df_salidas.groupby("Categoria_Plot")['Monto'].sum().reset_index()
                resumen_cat = resumen_cat.sort_values(by="Monto", ascending=False)
                
                st.bar_chart(data=resumen_cat.set_index("Categoria_Plot"), use_container_width=True)
                
                with st.expander("Ver desglose exacto de las categorías"):
                    st.dataframe(resumen_cat.rename(columns={"Categoria_Plot": "Clasificación", "Monto": "Total Gastado ($ MXN)"}), use_container_width=True)
            else:
                st.info("No hay salidas de caja registradas aún.")
        else:
            st.info("Aún no hay suficientes datos financieros para graficar.")
            
    except Exception as e:
        st.error(f"Error cargando el motor de analítica: {e}"
