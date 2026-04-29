import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. CONFIGURACIÓN SEGURA
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Falta la API Key en los Secrets.")

model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Asistente Ventas", layout="centered")

# 2. CARGA DE DATOS (Misma lógica pero con manejo de errores de red)
@st.cache_data(ttl=600)
def load_data():
    try:
        FILE_ID = "16HQlKYZavkZucbJQqLc4pHcwdK-ONH5wv-xWbEC4NTE"
        drive_url = f'https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv'
        df = pd.read_csv(drive_url)
        df.columns = df.columns.str.strip()
        df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
        return df
    except:
        return None

df = load_data()

st.title("📊 Asistente de Ventas")

# 3. INTERFAZ SIMPLIFICADA (Para evitar el error de Node)
# En lugar de st.chat_input dentro de bucles complejos, usamos una estructura lineal
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Contenedor para el historial (se dibuja primero)
chat_container = st.container()

with chat_container:
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]):
            st.write(m["content"])

# Entrada de usuario al final
prompt = st.chat_input("Pregunta algo sobre las ventas...")

if prompt:
    # 1. Mostrar mensaje del usuario
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with chat_container.chat_message("user"):
        st.write(prompt)

    # 2. Espacio reservado para la respuesta (Esto evita el error de removeChild)
    with chat_container.chat_message("assistant"):
        # USAMOS st.empty() PARA CONTROL TOTAL
        thinking_text = st.empty()
        data_placeholder = st.empty()
        desc_placeholder = st.empty()
        
        thinking_text.info("🔍 Procesando consulta...")
        
        try:
            # Lógica de la IA
            sys_prompt = f"Dataframe 'df' con: {df.columns.tolist()}. Responde SOLO código Python. Resultado en 'resultado'. Pregunta: {prompt}"
            raw_code = model.generate_content(sys_prompt).text
            clean_code = raw_code.replace('```python', '').replace('```', '').strip()
            
            # Ejecución
            loc = {'df': df, 'pd': pd}
            exec(clean_code, {}, loc)
            resultado = loc.get('resultado')

            # LIMPIAMOS el texto de carga antes de mostrar nada
            thinking_text.empty()

            # Mostramos los datos
            if isinstance(resultado, (pd.DataFrame, pd.Series)):
                data_placeholder.dataframe(resultado.head(10))
            else:
                data_placeholder.metric("Resultado", f"{resultado}")

            # Explicación
            desc_res = model.generate_content(f"Explica esto brevemente: {resultado}")
            desc_placeholder.write(desc_res.text)
            
            # Guardamos en historial
            st.session_state.chat_history.append({"role": "assistant", "content": desc_res.text})

        except Exception as e:
            thinking_text.empty()
            st.error("No pude entender esa consulta. Prueba con algo más simple.")
