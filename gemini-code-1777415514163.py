import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. CONFIGURACIÓN SEGURA (Usa los Secrets de Streamlit)
try:
    # Busca la clave que guardaste en los Settings de Streamlit Cloud
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ No se encontró la API Key en los Secrets de Streamlit.")

model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Asistente Ventas", layout="centered", page_icon="📊")

# 2. CARGA DE DATOS (Conexión Directa a Google Sheets)
@st.cache_data(ttl=600)
def load_data():
    try:
        # Tu ID de Google Sheets
        FILE_ID = "16HQlKYZavkZucbJQqLc4pHcwdK-ONH5wv-xWbEC4NTE"
        # URL formateada para exportar como CSV para que Pandas lo lea
        drive_url = f'https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv'
        
        df = pd.read_csv(drive_url)
        
        # Limpieza de nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Seleccionamos las columnas necesarias
        cols_validas = ['Fecha', 'Tienda', 'Producto', 'Categoria', 'Cantidad', 'Precio_Unitario', 'Total']
        df = df[cols_validas]
        
        # Limpieza de formatos de datos
        df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
        df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"❌ Error al conectar con los datos: {e}")
        return None

df = load_data()

# 3. INTERFAZ DE USUARIO
st.title("📊 Mi Asistente de Ventas")
st.markdown("Consulta tus datos en tiempo real.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Dibujamos el historial
chat_container = st.container()
for m in st.session_state.chat_history:
    with chat_container.chat_message(m["role"]):
        st.write(m["content"])

# 4. ENTRADA DE CONSULTAS
if prompt := st.chat_input("¿Qué quieres saber de tus ventas?"):
    # Guardar mensaje del usuario
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with chat_container.chat_message("user"):
        st.write(prompt)

    # Procesamiento
    with chat_container.chat_message("assistant"):
        # Contenedores para evitar errores visuales (removeChild)
        status_placeholder = st.empty()
        data_placeholder = st.empty()
        
        status_placeholder.info("🔍 Analizando base de datos...")
        
        try:
            # Prompt para Gemini
            sys_prompt = f"""
            Actúa como experto en Pandas. Tienes un DataFrame 'df' con columnas: {df.columns.tolist()}.
            Reglas:
            1. Responde SOLO código Python.
            2. El resultado debe guardarse en la variable 'resultado'.
            3. Si es un ranking o lista, usa .head(10).
            Pregunta: {prompt}
            """
            
            raw_res = model.generate_content(sys_prompt).text
            # Limpiamos el código por si trae markdown
            codigo = raw_res.replace('```python', '').replace('```', '').strip()
            
            # --- EJECUCIÓN SEGURA (Solución al NameError: 'df') ---
            entorno = {'df': df, 'pd': pd}
            exec(codigo, entorno)
            resultado = entorno.get('resultado')

            # Si no encontró 'resultado', buscamos cualquier variable nueva
            if resultado is None:
                vars_nuevas = {k: v for k, v in entorno.items() if k not in ['df', 'pd', '__builtins__']}
                if vars_nuevas:
                    resultado = list(vars_nuevas.values())[-1]

            status_placeholder.empty() # Quitamos el "Analizando..."

            # Mostramos los datos encontrados
            if isinstance(resultado, (pd.DataFrame, pd.Series)):
                data_placeholder.dataframe(resultado)
            else:
                data_placeholder.metric("Valor", f"{resultado}")

            # Explicación breve de la IA
            explicacion = model.generate_content(f"Explica brevemente este dato de ventas: {resultado}").text
            st.write(explicacion)
            
            # Guardamos en el historial
            st.session_state.chat_history.append({"role": "assistant", "content": explicacion})

        except Exception as e:
            status_placeholder.empty()
            st.error("No pude completar el cálculo. Intenta ser más específico.")
            with st.expander("Ver detalle del error"):
                st.write(e)
