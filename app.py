import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# 1. Configuración de página y estilos personalizados (Tema Invertido / Claro)
st.set_page_config(page_title="Soccer Buddy LITE", layout="wide", page_icon="⚽")

# Forzar estilos visuales acordes al nuevo logotipo con fondo claro
st.markdown("""
    <style>
        /* Fondo principal de la app y barra lateral */
        .stApp { background-color: #fcfbf7; }
        [data-testid="stSidebar"] { background-color: #f5f2eb; }
        
        /* Modificar color de títulos y textos */
        h1, h2, h3, h4, p, span { color: #04291e !important; }
        
        /* Ajustar inputs numéricos y sliders */
        .stSlider, .stNumberInput { color: #04291e; }
    </style>
""", unsafe_allow_html=True)

DB_FILE = "historial_lite_analytics.csv"
FC_MAX_HISTORICA = 195  # Ajusta según tu frecuencia cardíaca máxima real

# Cargar o inicializar la base de datos local
if os.path.exists(DB_FILE):
    df_historial = pd.read_csv(DB_FILE)
    df_historial['Fecha'] = pd.to_datetime(df_historial['Fecha'])
else:
    df_historial = pd.DataFrame(columns=[
        "Fecha", "Tipo Sesión", "Duración (min)", "Esfuerzo (1-10)",
        "Distancia (km)", "Velocidad Máx (km/h)", "Sprints", 
        "FC Promedio (bpm)", "FC Máxima (bpm)", "Calorías Activas (kcal)",
        "Carga sRPE", "Carga TRIMP", "Eficiencia CV", "Densidad Sprints (sp/min)", "Distancia HSR Est (m)"
    ])

# --- BARRA LATERAL CON EL LOGOTIPO ---
with st.sidebar:
    logo_path = "logo_lite.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.warning("⚠️ Archivo 'logo_lite.png' no encontrado en el directorio.")
    
    st.divider()
    st.markdown("### **Soccer Buddy LITE**")
    st.caption("Módulo de monitoreo temporal optimizado para Apple Watch y Pitch Pulse data.")
    st.info("💡 Diseñado para Fernando Velez Fisioterapia")

# --- CUERPO PRINCIPAL ---
st.title("⚽ Soccer Buddy - Versión LITE Pro")
st.subheader("Análisis de Carga de Trabajo y Semáforo de Riesgo de Lesión")

col_form, col_dash = st.columns([1, 1.2])

# --- 2. FORMULARIO DE ENTRADA MANUAL ---
with col_form:
    st.write("### 📝 Registrar Nueva Sesión")
    with st.form("form_registro", clear_on_submit=True):
        fecha = st.date_input("Fecha de la Sesión", datetime.today())
        tipo_sesion = st.selectbox("Tipo de Sesión", ["Partido Completo", "Fútbol 5/7", "Entrenamiento Intensivo", "Gimnasio/Físico"])
        duracion = st.number_input("Duración Total (minutos)", min_value=1, max_value=300, value=60)
        esfuerzo = st.slider("Esfuerzo Percibido (sRPE) - Escala de 1 al 10", 1, 10, 7)
        
        st.divider()
        st.write("**Métricas Físicas:**")
        distancia = st.number_input("Distancia Total (km)", min_value=0.0, max_value=30.0, value=6.2, step=0.1)
        vel_max = st.number_input("Velocidad Máxima (km/h)", min_value=0.0, max_value=45.0, value=24.5, step=0.1)
        sprints = st.number_input("Sprints Realizados", min_value=0, max_value=100, value=12)
        
        st.divider()
        st.write("**Métricas Cardiovasculares:**")
        fc_prom = st.number_input("Frecuencia Cardíaca Promedio (bpm)", min_value=40, max_value=220, value=152)
        fc_max = st.number_input("Frecuencia Cardíaca Máxima (bpm)", min_value=40, max_value=220, value=182)
        calorias = st.number_input("Calorías Activas (kcal)", min_value=0, max_value=2500, value=650)
        
        submit = st.form_submit_button("Calcular y Guardar en Historial")
        
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
            df_historial.to_csv(DB_FILE, index=False)
            st.success("¡Métricas integradas con éxito!")
            st.rerun()

# --- 3. PANEL DE CONTROL Y MODELO DE LESIONES ACWR ---
with col_dash:
    if not df_historial.empty:
        st.write("### 🛡️ Semáforo de Riesgo de Lesión (ACWR)")
        
        # Ordenar cronológicamente
        df_historial = df_historial.sort_values(by="Fecha").reset_index(drop=True)
        ultima_fecha = df_historial["Fecha"].max()
        
        # Ventanas Aguda (7 días) y Crónica (28 días)
        carga_aguda = df_historial[df_historial["Fecha"] >= (ultima_fecha - timedelta(days=7))]["Carga TRIMP"].sum()
        carga_cronica_total = df_historial[df_historial["Fecha"] >= (ultima_fecha - timedelta(days=28))]["Carga TRIMP"].sum()
        
        carga_cronica_promedio = carga_cronica_total / 4 if carga_cronica_total > 0 else 1
        acwr = round(carga_aguda / carga_cronica_promedio, 2) if carga_cronica_promedio > 0 else 0
        
        # Clasificación del Semáforo
        if acwr < 0.8:
            estado_semaforo = "🟢 BAJO (Sub-entrenamiento)"
            color_banner = "#2ecc71"
            detalle_semaforo = "Estás entrenando por debajo de tu base crónica. Riesgo bajo por fatiga, pero podrías perder condición."
        elif 0.8 <= acwr <= 1.3:
            estado_semaforo = "🟢 ÓPTIMO (Zona Dulce)"
            color_banner = "#27ae60"
            detalle_semaforo = "¡Perfecto! Nivel ideal de estímulo físico adaptativo con riesgo mínimo de lesión estructural."
        elif 1.3 < acwr <= 1.5:
            estado_semaforo = "🟡 MODERADO (Alerta de Fatiga)"
            color_banner = "#f1c40f"
            detalle_semaforo = "Zona de precaución. La carga subió rápido esta semana. Revisa sobrecargas musculares."
        else:
            estado_semaforo = "🔴 PELIGRO (Riesgo Crítico de Lesión)"
            color_banner = "#e74c3c"
            detalle_semaforo = "¡Cuidado! Incremento drástico de fatiga a corto plazo. Se sugiere sesión de descarga activa o descanso."

        # Renderizado del bloque del Semáforo
        st.markdown(f"""
        <div style="background-color:{color_banner}; padding:18px; border-radius:8px; text-align:center;">
            <h2 style="color:white !important; margin:0; font-weight: bold;">Ratio ACWR: {acwr}</h2>
            <h4 style="color:white !important; margin:5px 0 0 0;">{estado_semaforo}</h4>
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"ℹ️ *{detalle_semaforo}*")
        
        # Métricas de la última sesión
        st.write("### 📊 Indicadores Avanzados Calculados (Último Registro)")
        ultima_sesion = df_historial.iloc[-1]
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Carga TRIMP", f"{ultima_sesion['Carga TRIMP']}")
        m2.metric("Eficiencia CV", f"{ultima_sesion['Eficiencia CV']} m/bpm")
        m3.metric("Densidad Sprints", f"{ultima_sesion['Densidad Sprints (sp/min)']} sp/m")
        m4.metric("Est. Trabajo HSR", f"{int(ultima_sesion['Distancia HSR Est (m)'])} m")

        # Gráfica evolutiva
        st.write("### 📈 Tendencia de Carga Física vs Cardio")
        st.line_chart(df_historial.set_index("Fecha")[["Carga TRIMP", "Carga sRPE"]])
        
        st.write("### 📅 Historial General de Sesiones")
        # Mostrar tabla ordenada con las más recientes primero
        df_mostrar = df_historial.copy()
        df_mostrar['Fecha'] = df_mostrar['Fecha'].dt.strftime('%Y-%m-%d')
        st.dataframe(df_mostrar.sort_values(by="Fecha", ascending=False), use_container_width=True)
        
    else:
        st.info("👋 ¡Bienvenido! Ingresa la sesión de hoy en el formulario para activar el modelo dinámico y el semáforo de riesgo.")
