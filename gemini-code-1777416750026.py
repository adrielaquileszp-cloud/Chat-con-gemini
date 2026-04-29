import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. CONFIGURACIÓN (Segura con Secrets)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Configura GEMINI_API_KEY en los Secrets de Streamlit.")

model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Asistente Ventas", layout="centered")

# 2. CARGA DE DATOS
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
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        return df
    except Exception as e:
        return None

df = load_data()

st.title("📊 Asistente de Ventas")

# 3. MANEJO DEL HISTORIAL (Sin duplicados ni errores de renderizado)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Dibujar el historial de forma estática
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 4. ENTRADA DE USUARIO
if prompt := st.chat_input("¿Qué quieres consultar?"):
    # Mostrar inmediatamente el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Lógica de respuesta
    with st.chat_message("assistant"):
        # Usamos placeholders vacíos para que Streamlit no se confunda al renderizar
        status_placeholder = st.empty()
        response_placeholder = st.empty()
        
        status_placeholder.write("⌛ Analizando datos...")
        
        try:
            # Prompt para la IA
            sys_prompt = f"Dataframe 'df' columnas: {df.columns.tolist()}. Responde SOLO con código Python. Resultado en variable 'resultado'. Pregunta: {prompt}"
            
            raw_res = model.generate_content(sys_prompt).text
            codigo = raw_res.replace('```python', '').replace('```', '').strip()
            
            loc = {'df': df, 'pd': pd}
            exec(codigo, {}, loc)
            resultado = loc.get('resultado')

            # Limpiamos el mensaje de "Analizando..." antes de poner el resultado
            status_placeholder.empty()

            # Mostramos el resultado
            if isinstance(resultado, (pd.DataFrame, pd.Series)):
                response_placeholder.dataframe(resultado.head(15))
            else:
                response_placeholder.metric("Resultado", f"{resultado}")

            # Explicación final
            exp = model.generate_content(f"Resume este dato: {resultado}").text
            st.write(exp)
            
            # Guardamos la explicación en el historial
            st.session_state.messages.append({"role": "assistant", "content": exp})

        except Exception as e:
            status_placeholder.empty()
            st.error("No pude procesar la consulta.")
