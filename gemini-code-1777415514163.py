import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. CONFIGURACIÓN DE SEGURIDAD (Usa los Secrets de Streamlit Cloud)
try:
    # Asegúrate de haber guardado GEMINI_API_KEY en Settings -> Secrets
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ Error: Configura 'GEMINI_API_KEY' en los Secrets de Streamlit.")

model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Asistente Ventas", layout="centered", page_icon="📊")

# 2. CARGA DE DATOS DESDE GOOGLE SHEETS
@st.cache_data(ttl=600) # Actualiza cada 10 min
def load_data():
    try:
        # Tu ID de documento de Google Sheets
        FILE_ID = "16HQlKYZavkZucbJQqLc4pHcwdK-ONH5wv-xWbEC4NTE"
        drive_url = f'https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv'
        
        df = pd.read_csv(drive_url)
        
        # Limpieza profunda de columnas
        df.columns = df.columns.str.strip()
        cols_validas = ['Fecha', 'Tienda', 'Producto', 'Categoria', 'Cantidad', 'Precio_Unitario', 'Total']
        df = df[cols_validas]
        
        # Formateo de datos
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

# Dibujamos el historial de forma estable
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
        # Placeholders para evitar errores de renderizado (removeChild)
        status_placeholder = st.empty()
        data_placeholder = st.empty()
        
        status_placeholder.info("🔍 Analizando datos...")
        
        # Prompt Ultra-Estricto para la IA
        sys_prompt = f"""
        Eres un experto en Python y Pandas. 
        Tienes un DataFrame llamado 'df' con estas columnas: {df.columns.tolist()}
        
        REGLAS OBLIGATORIAS:
        1. Responde ÚNICAMENTE con código Python funcional.
        2. El resultado final DEBE estar asignado a una variable llamada 'resultado'.
        3. NO uses print() ni texto explicativo.
        4. Si es una lista o ranking, usa .head(10).
        
        Pregunta: {prompt}
        """

        try:
            # Obtener código de Gemini
            response_ia = model.generate_content(sys_prompt).text
            codigo = response_ia.replace('```python', '').replace('```', '').strip()
            
            # --- EJECUCIÓN BLINDADA ---
            # Pasamos df y pd explícitamente en el diccionario de ejecución
            entorno = {'df': df, 'pd': pd}
            exec(codigo, entorno)
            
            # Buscamos el resultado calculado
            resultado = entorno.get('resultado')
            
            # Plan B: Si la IA cambió el nombre de la variable por error
            if resultado is None:
                vars_nuevas = {k: v for k, v in entorno.items() if k not in ['df', 'pd', '__builtins__']}
                if vars_nuevas:
                    resultado = list(vars_nuevas.values())[-1]

            status_placeholder.empty()

            # Mostrar resultado visual
            if isinstance(resultado, (pd.DataFrame, pd.Series)):
                data_placeholder.dataframe(resultado)
            elif isinstance(resultado, (int, float)):
                data_placeholder.metric("Resultado", f"${resultado:,.2f}")
            else:
                data_placeholder.info(f"Resultado: {resultado}")

            # Explicación en lenguaje natural
            desc_ia = model.generate_content(f"Explica brevemente este dato de ventas: {resultado} para la duda
