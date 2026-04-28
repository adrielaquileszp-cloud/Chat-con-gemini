import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. Configuración de la API de Gemini
genai.configure(api_key="TU_API_KEY_AQUI")
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("📊 Asistente de Ventas")

# 2. Cargar los datos (usamos cache para que sea rápido)
@st.cache_data
def load_data():
    df = pd.read_csv("Ventas Asistente - Ventas.csv")
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    return df

df = load_data()

# 3. Interfaz de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("¿Qué quieres saber de las ventas?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 4. Lógica de Análisis
    # Aquí es donde ocurre la magia: extraemos datos relevantes para dárselos a la IA
    # Ejemplo: Si el usuario pregunta por una tienda, filtramos el DF
    resumen_datos = df.describe().to_string() # Esto es un ejemplo simple
    
    # Consulta a Gemini
    contexto = f"Datos actuales: {df.head(10).to_string()}... (total {len(df)} filas)"
    response = model.generate_content(f"Basado en estos datos: {contexto}. Responde a la pregunta: {prompt}")

    with st.chat_message("assistant"):
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})