import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. CONFIGURACIÓN DE SEGURIDAD
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    
    # Intentamos cargar el modelo. Si falla el nombre 'gemini-1.5-flash', 
    # el sistema saltará automáticamente a 'gemini-pro'.
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        model = genai.GenerativeModel('gemini-pro')
        
except Exception as e:
    st.error("⚠️ Configura 'GEMINI_API_KEY' en los Secrets de Streamlit.")

st.set_page_config(page_title="Asistente Ventas", layout="centered", page_icon="📊")

# 2. CARGA DE DATOS
@st.cache_data(ttl=300)
def load_data():
    try:
        FILE_ID = "16HQlKYZavkZucbJQqLc4pHcwdK-ONH5wv-xWbEC4NTE"
        # URL de exportación CSV directa
        url = f'https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv'
        df = pd.read_csv(url)
        
        # Limpieza de columnas
        df.columns = df.columns.str.strip()
        cols = ['Fecha', 'Tienda', 'Producto', 'Categoria', 'Cantidad', 'Precio_Unitario', 'Total']
        df = df[cols]
        
        # Formateo
        df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets: {e}")
        return None

df = load_data()

# 3. INTERFAZ
st.title("📊 Mi Asistente de Ventas")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

chat_container = st.container()
for m in st.session_state.chat_history:
    with chat_container.chat_message(m["role"]):
        st.write(m["content"])

# 4. CHAT
if prompt := st.chat_input("¿Qué quieres saber?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with chat_container.chat_message("user"):
        st.write(prompt)

    if df is not None:
        with chat_container.chat_message("assistant"):
            st_status = st.empty()
            st_status.info("🔍 Analizando...")
            
            try:
                # Instrucción para la IA
                sys_msg = f"Actúa como experto en Pandas. DataFrame 'df' con columnas: {df.columns.tolist()}. Responde SOLO código Python. El resultado debe estar en la variable 'resultado'. Pregunta: {prompt}"
                
                # Generar código usando el modelo configurado
                response = model.generate_content(sys_msg)
                codigo = response.text.replace('```python', '').replace('```', '').strip()
                
                # Ejecutar código
                entorno = {'df': df, 'pd': pd}
                exec(codigo, entorno)
                resultado = entorno.get('resultado')

                st_status.empty()

                if isinstance(resultado, (pd.DataFrame, pd.Series)):
                    st.dataframe(resultado.head(10))
                else:
                    st.metric("Resultado", f"{resultado}")

                # Explicación
                explicacion = model.generate_content(f"Resume este dato brevemente: {resultado}").text
                st.write(explicacion)
                st.session_state.chat_history.append({"role": "assistant", "content": explicacion})

            except Exception as e:
                st_status.empty()
                st.error("Hubo un detalle técnico. Intenta de nuevo.")
                with st.expander("Ver error"):
                    st.write(e)
