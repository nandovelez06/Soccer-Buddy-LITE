import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# 1. Configuración de página y estilos personalizados (Modo Oscuro Puro)
st.set_page_config(page_title="Soccer Buddy LITE", layout="wide", page_icon="⚽")

# Forzar estilos visuales en modo oscuro negro absoluto y barra lateral verde institucional
st.markdown("""
    <style>
        /* Fondo principal de la app (Negro Puro) y barra lateral (Verde Oscuro) */
        .stApp { background-color: #0d0d0d; }
        [data-testid="stSidebar"] { background-color: #031711; }
        
        /* Modificar color de títulos, etiquetas y textos a blanco/crema */
        h1, h2, h3, h4, p, span, label { color: #f5f2eb !important; }
        
        /* Ajustar bordes, textos e inputs de formularios */
        .stSlider, .stNumberInput, .stSelectbox, .stDateInput { color: #f5f2eb; }
        
        /* Fondo de los contenedores de datos (Metrics) para alta visibilidad */
        div[data-testid="stMetricBlock"] {
            background-color: #07261d;
            border: 1px solid #0d4234;
            border-radius: 8px;
            padding: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Nombre de la base de datos cambiada a formato Excel (.xlsx)
DB_FILE = "historial_lite_analytics.xlsx"
FC_MAX_HISTORICA = 195  # Ajusta según tu frecuencia cardíaca máxima real

# Cargar o inicializar la base de datos local en Excel
if os.path.exists(DB_FILE):
    df_historial = pd.read_excel(DB_FILE)
    df_historial['Fecha'] = pd.to_datetime(df_historial['Fecha'])
else:
    df_historial = pd.DataFrame(columns=[
        "Fecha", "Tipo Sesión", "Duración (min)", "Esfuerzo (1-10)",
        "Distancia (km)", "Velocidad Máx (km/h)", "Sprints", 
        "FC Promedio (bpm)", "FC Máxima (bpm)", "Calorías Activas (kcal)",
        "Carga sRPE", "Carga TRIMP", "Eficiencia CV", "Densidad Sprints (sp/min)", "Distancia HSR Est (m)"
    ])

# --- BARRA LATERAL IZQUIERDA: LOGO + FORMULARIO DE DATOS ---
with st.sidebar:
    logo_path = "logo_lite.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.warning("⚠️ Archivo 'logo_lite.png' no encontrado.")
    
    st.divider()
    st.markdown("### 📝 Registrar Nueva Sesión")
    
    # Formulario compacto dentro de la barra lateral desplegable
    with st.form("form_registro", clear_on_submit=True):
        fecha = st.date_input("Fecha de la Sesión", datetime.today())
        tipo_sesion = st.selectbox("Tipo de Sesión", ["Partido Completo", "Fútbol 5/7", "Entrenamiento Intensivo", "Gimnasio/Físico"])
        duracion = st.number_input("Duración Total (minutos)", min_value=1, max_value=300, value=60)
        esfuerzo = st.slider("Esfuerzo Percibido (sRPE)", 1, 10, 7)
        
        st.markdown("**Métricas Físicas:**")
        distancia = st.number_input("Distancia Total (km)", min_value=0.0, max_value=30.0, value=6.2, step=0.1)
        vel_max = st.number_input("Velocidad Máxima (km/h)", min_value=0.0, max_value=45.0, value=24.5, step=0.1)
        sprints = st.number_input("Sprints Realizados", min_value=0, max_value=100, value=12)
        
        st.markdown("**Métricas Cardiovasculares:**")
        fc_prom = st.number_input("Frecuencia Cardíaca Promedio (bpm)", min_value=40, max_value=220, value=152)
        fc_max = st.number_input("Frecuencia Cardíaca Máxima (bpm)", min_value=40, max_value=220, value=182)
        calorias = st.number_input("Calorías Activas (kcal)", min_value=0, max_value=2500, value=650)
        
        submit = st.form_submit_button("Guardar en Historial Excel")
        
        if submit:
            # --- FÓRMULAS AVANZADAS ---
            carga_srpe = duracion * esfuerzo
            carga_trimp = duracion * (fc_prom / FC_MAX_HISTORICA)
            eficiencia_cv = round((distancia * 1000) / fc_prom, 2) if fc_prom > 0 else 0
            densidad_sprints = round(sprints / duracion, 2) if duracion > 0 else 0
            distancia_hsr_est = round((distancia * 1000) * 0.10, 1)
            
            nueva_fila = {
                "Fecha": pd.to_datetime(fecha),
                "Tipo Sesión": tipo_sesion,
                "Duración (min)": duracion,
                "Esfuerzo (1-10)": esfuerzo,
                "Distancia (km)": distancia,
                "Velocidad Máx (km/h)": vel_max,
                "Sprints": sprints,
                "FC Promedio (bpm)": fc_prom,
                "FC Máxima (bpm)": fc_max,
                "Calorías Activas (kcal)": calorias,
                "Carga sRPE": carga_srpe,
                "Carga TRIMP": round(carga_trimp, 2),
                "Eficiencia CV": eficiencia_cv,
                "Densidad Sprints (sp/min)": densidad_sprints,
                "Distancia HSR Est (m)": distancia_hsr_est
            }
            
            df_historial = pd.concat([df_historial, pd.DataFrame([nueva_fila])], ignore_index=True)
            # Escritura limpia en el motor de Excel openpyxl
            df_historial.to_excel(DB_FILE, index=False, engine='openpyxl')
            st.success("¡Métricas guardadas en el Excel!")
            st.rerun()

# --- CUERPO PRINCIPAL (DASHBOARD TOTALMENTE OSCURO) ---
st.title("⚽ Soccer Buddy - Versión LITE Pro")
st.subheader("Panel de Rendimiento Físico y Riesgo de Lesión")

if not df_historial.empty:
    st.write("### 🛡️ Semáforo de Riesgo de Lesión (ACWR)")
    
    # Ordenar cronológicamente las cargas
    df_historial = df_historial.sort_values(by="Fecha").reset_index(drop=True)
    ultima_fecha = df_historial["Fecha"].max()
    
    # Ventanas Aguda (7 días) y Crónica (28 días)
    carga_aguda = df_historial[df_historial["Fecha"] >= (ultima_fecha - timedelta(days=7))]["Carga TRIMP"].sum()
    carga_cronica_total = df_historial[df_historial["Fecha"] >= (ultima_fecha - timedelta(days=28))]["Carga TRIMP"].sum()
    
    carga_cronica_promedio = carga_cronica_total / 4 if carga_cronica_total > 0 else 1
    acwr = round(carga_aguda / carga_cronica_promedio, 2) if carga_cronica_promedio > 0 else 0
    
    # Clasificación del Semáforo Científico
    if acwr < 0.8:
        estado_semaforo = "🟢 BAJO (Sub-entrenamiento)"
        color_banner = "#2ecc71"
        detalle_semaforo = "Estás entrenando por debajo de tu base crónica. Riesgo bajo por fatiga, pero podrías perder condición física."
    elif 0.8 <= acwr <= 1.3:
        estado_semaforo = "🟢 ÓPTIMO (Zona Dulce)"
        color_banner = "#27ae60"
        detalle_semaforo = "¡Perfecto! Nivel ideal de estímulo físico adaptativo con riesgo mínimo de lesión estructural."
    elif 1.3 < acwr <= 1.5:
        estado_semaforo = "🟡 MODERADO (Alerta de Fatiga)"
        color_banner = "#f1c40f"
        detalle_semaforo = "Zona de precaución. La carga de entrenamiento subió muy rápido esta semana. Revisa sobrecargas musculares."
    else:
        estado_semaforo = "🔴 PELIGRO (Riesgo Crítico de Lesión)"
        color_banner = "#e74c3c"
        detalle_semaforo = "¡Cuidado! Incremento drástico de fatiga a corto plazo. Se sugiere sesión de descarga activa o descanso absoluto."

    # Renderizado del bloque del Semáforo
    st.markdown(f"""
    <div style="background-color:{color_banner}; padding:18px; border-radius:8px; text-align:center; margin-bottom: 20px;">
        <h2 style="color:white !important; margin:0; font-weight: bold;">Ratio ACWR: {acwr}</h2>
        <h4 style="color:white !important; margin:5px 0 0 0;">{estado_semaforo}</h4>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"ℹ️ *{detalle_semaforo}*")
    
    st.divider()
    
    # Métricas de la última sesión ingresada
    st.write("### 📊 Indicadores Avanzados Calculados (Último Registro)")
    ultima_sesion = df_historial.iloc[-1]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Carga TRIMP", f"{ultima_sesion['Carga TRIMP']}")
    m2.metric("Eficiencia CV", f"{ultima_sesion['Eficiencia CV']} m/bpm", help="Metros avanzados por latido cardíaco.")
    m3.metric("Densidad Sprints", f"{ultima_sesion['Densidad Sprints (sp/min)']} sp/m")
    m4.metric("Est. Trabajo HSR", f"{int(ultima_sesion['Distancia HSR Est (m)'])} m")

    st.divider()

    # Gráfica evolutiva
    st.write("### 📈 Tendencia de Carga Física vs Carga Cardiovascular")
    st.line_chart(df_historial.set_index("Fecha")[["Carga TRIMP", "Carga sRPE"]])
    
    st.divider()
    
    st.write("### 📅 Historial General de Sesiones")
    df_mostrar = df_historial.copy()
    df_mostrar['Fecha'] = df_mostrar['Fecha'].dt.strftime('%Y-%m-%d')
    st.dataframe(df_mostrar.sort_values(by="Fecha", ascending=False), use_container_width=True)
    
else:
    st.info("👋 ¡Módulo LITE activo! Despliega la barra lateral izquierda e ingresa tu primera sesión para inicializar el libro de Excel y el semáforo dinámico.")
