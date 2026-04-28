import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. CONFIGURACIÓN DE SEGURIDAD Y API
# SUSTITUYE POR TU NUEVA CLAVE GENERADA
API_KEY = "TU_NUEVA_API_KEY"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Asistente Ventas", layout="centered", page_icon="📊")

# 2. CARGA Y LIMPIEZA DE DATOS (Conexión Directa a Google Sheets)
@st.cache_data(ttl=600) # Se actualiza cada 10 minutos
def load_data():
    try:
        # ID de tu documento que proporcionaste
        FILE_ID = "16HQlKYZavkZucbJQqLc4pHcwdK-ONH5wv-xWbEC4NTE"
        # URL formateada para exportación CSV
        drive_url = f'https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv'
        
        # Lectura de datos
        df = pd.read_csv(drive_url)
        
        # Limpieza de nombres de columnas (quitar espacios invisibles)
        df.columns = df.columns.str.strip()
        
        # Seleccionamos las columnas necesarias
        cols_validas = ['Fecha', 'Tienda', 'Producto', 'Categoria', 'Cantidad', 'Precio_Unitario', 'Total']
        df = df[cols_validas]
        
        # Convertir tipos de datos para evitar errores en cálculos
        df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
        df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return None

df = load_data()

# 3. INTERFAZ DE USUARIO
st.title("📊 Asistente de Ventas Real-Time")
st.markdown("Consulta tus datos de Google Sheets usando lenguaje natural.")

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. LÓGICA DEL CHAT
if prompt := st.chat_input("¿Qué quieres consultar?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    if df is not None:
        with st.spinner("Calculando desde la nube..."):
            # Prompt estricto para que Gemini solo devuelva código
            sys_prompt = f"""
            Eres un experto en Python y Pandas.
            Dataframe 'df' con columnas: {df.columns.tolist()}
            
            REGLAS:
            1. Responde ÚNICAMENTE con código Python funcional.
            2. El resultado final DEBE guardarse en la variable 'resultado'.
            3. No uses bloques de texto ni explicaciones.
            
            Pregunta: {prompt}
            """

            try:
                # Generar código
                raw_response = model.generate_content(sys_prompt).text
                codigo = raw_response.replace('```python', '').replace('```', '').strip()
                
                # Ejecutar código
                loc = {'df': df, 'pd': pd}
                exec(codigo, {}, loc)
                
                # Obtener resultado
                resultado = loc.get('resultado')
                
                # Si 'resultado' no existe, buscar la última variable creada
                if resultado is None:
                    vars_creadas = [v for k, v in loc.items() if k not in ['df', 'pd']]
                    resultado = vars_creadas[-1] if vars_creadas else "No hay datos."

                # Mostrar en pantalla
                with st.chat_message("assistant"):
                    # Contenedor para evitar errores de renderizado en móvil
                    res_container = st.container()
                    
                    if isinstance(resultado, (pd.DataFrame, pd.Series)):
                        res_container.dataframe(resultado.head(20), use_container_width=True)
                    elif isinstance(resultado, (int, float)):
                        res_container.metric("Total", f"${resultado:,.2f}")
                    else:
                        res_container.write(f"Resultado: {resultado}")

                    # Breve explicación humana
                    explicacion = model.generate_content(f"Resume este resultado de ventas: {resultado}")
                    res_container.info(explicacion.text)
                    
                    st.session_state.messages.append({"role": "assistant", "content": explicacion.text})

            except Exception as e:
                st.error("No pude interpretar la consulta. Prueba con algo más directo.")
                with st.expander("Detalle técnico"):
                    st.code(codigo)
                    st.write(e)
    else:
        st.error("No hay datos disponibles para consultar.")
