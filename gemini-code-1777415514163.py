import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. CONFIGURACIÓN (Actualizada a Gemini 3.0)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # Usamos el modelo que tu diagnóstico confirmó como disponible
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
except Exception:
    st.error("⚠️ Configura 'GEMINI_API_KEY' en los Secrets.")

st.set_page_config(page_title="Asistente Ventas 3.0", layout="centered")

# 2. CARGA DE DATOS (URL Directa)
@st.cache_data(ttl=300)
def load_data():
    try:
        FILE_ID = "16HQlKYZavkZucbJQqLc4pHcwdK-ONH5wv-xWbEC4NTE"
        url = f'https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv'
        df = pd.read_csv(url)
        
        # Limpieza de columnas (ignorando las basura del final)
        df.columns = df.columns.str.strip()
        cols_reales = ['Fecha', 'Tienda', 'Producto', 'Categoria', 'Cantidad', 'Precio_Unitario', 'Total']
        df = df[cols_reales]
        
        # Formateo
        df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"❌ Error en datos: {e}")
        return None

df = load_data()

st.title("🚀 Asistente de Ventas 3.0")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Historial
chat_container = st.container()
for m in st.session_state.chat_history:
    with chat_container.chat_message(m["role"]):
        st.write(m["content"])

# 4. CHAT
if prompt := st.chat_input("Pregunta lo que quieras sobre las ventas..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with chat_container.chat_message("user"):
        st.write(prompt)

    if df is not None:
        with chat_container.chat_message("assistant"):
            st_status = st.empty()
            st_status.info("✨ Pensando con Gemini 3.0 Flash...")
            
            try:
                # Instrucción para la IA
                sys_msg = f"Actúa como experto en Pandas. DataFrame 'df' con columnas: {df.columns.tolist()}. Responde SOLO código Python. El resultado final en la variable 'resultado'. Pregunta: {prompt}"
                
                # Generar código
                response = model.generate_content(sys_msg)
                codigo = response.text.replace('```python', '').replace('```', '').strip()
                
                # Ejecutar
                entorno = {'df': df, 'pd': pd}
                exec(codigo, entorno)
                resultado = entorno.get('resultado')

                st_status.empty()

                if isinstance(resultado, (pd.DataFrame, pd.Series)):
                    st.dataframe(resultado.head(15))
                else:
                    st.metric("Resultado", f"{resultado}")

                # Explicación
                explicacion = model.generate_content(f"Resume brevemente este dato: {resultado}").text
                st.write(explicacion)
                st.session_state.chat_history.append({"role": "assistant", "content": explicacion})

            except Exception as e:
                st_status.empty()
                st.error("Detalle al procesar.")
                with st.expander("Ver detalle técnico"):
                    st.write(e)
