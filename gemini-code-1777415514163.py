import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. CONFIGURACIÓN DE SEGURIDAD (Usa los Secrets de Streamlit Cloud)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ Error: Configura 'GEMINI_API_KEY' en los Secrets de Streamlit.")

model = genai.GenerativeModel('models/gemini-1.5-flash')

st.set_page_config(page_title="Asistente Ventas", layout="centered", page_icon="📊")

# 2. CARGA DE DATOS DESDE GOOGLE SHEETS
@st.cache_data(ttl=600)
def load_data():
    try:
        FILE_ID = "16HQlKYZavkZucbJQqLc4pHcwdK-ONH5wv-xWbEC4NTE"
        drive_url = f'https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv'
        df = pd.read_csv(drive_url)
        
        df.columns = df.columns.str.strip()
        cols_validas = ['Fecha', 'Tienda', 'Producto', 'Categoria', 'Cantidad', 'Precio_Unitario', 'Total']
        df = df[cols_validas]
        
        df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
        df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets: {e}")
        return None

df = load_data()

# 3. INTERFAZ DE USUARIO
st.title("📊 Mi Asistente de Ventas")
st.markdown("Consulta tus datos en vivo desde Google Sheets.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

chat_container = st.container()
for m in st.session_state.chat_history:
    with chat_container.chat_message(m["role"]):
        st.write(m["content"])

# 4. LÓGICA DE CONSULTAS
if prompt := st.chat_input("¿Qué quieres saber de tus ventas?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with chat_container.chat_message("user"):
        st.write(prompt)

    with chat_container.chat_message("assistant"):
        status_placeholder = st.empty()
        data_placeholder = st.empty()
        
        status_placeholder.info("🔍 Analizando datos...")
        
        sys_prompt = f"""
        Eres un experto en Python y Pandas. 
        Tienes un DataFrame llamado 'df' con estas columnas: {df.columns.tolist() if df is not None else []}
        
        REGLAS OBLIGATORIAS:
        1. Responde ÚNICAMENTE con código Python funcional.
        2. El resultado final DEBE estar asignado a una variable llamada 'resultado'.
        3. NO uses print() ni texto explicativo.
        4. Si es una lista o ranking, usa .head(10).
        
        Pregunta: {prompt}
        """

        try:
            response_ia = model.generate_content(sys_prompt).text
            codigo = response_ia.replace('```python', '').replace('```', '').strip()
            
            entorno = {'df': df, 'pd': pd}
            exec(codigo, entorno)
            
            resultado = entorno.get('resultado')
            
            if resultado is None:
                vars_nuevas = {k: v for k, v in entorno.items() if k not in ['df', 'pd', '__builtins__']}
                if vars_nuevas:
                    resultado = list(vars_nuevas.values())[-1]

            status_placeholder.empty()

            if isinstance(resultado, (pd.DataFrame, pd.Series)):
                data_placeholder.dataframe(resultado)
            elif isinstance(resultado, (int, float)):
                data_placeholder.metric("Resultado", f"${resultado:,.2f}")
            else:
                data_placeholder.info(f"Resultado: {resultado}")

            # LINEA CORREGIDA (Aquí estaba el error de sintaxis)
            desc_ia = model.generate_content(f"Explica brevemente este dato: {resultado} para la duda: {prompt}")
            st.write(desc_ia.text)
            
            st.session_state.chat_history.append({"role": "assistant", "content": desc_ia.text})

        except Exception as e:
            status_placeholder.empty()
            st.error("Lo siento, no pude procesar esa consulta.")
            with st.expander("Detalle técnico"):
                st.write(e)
