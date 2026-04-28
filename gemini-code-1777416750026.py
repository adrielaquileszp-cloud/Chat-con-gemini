import streamlit as st
import pandas as pd
import google.generativeai as genai
import re

# 1. CONFIGURACIÓN DE SEGURIDAD Y API
# Reemplaza con tu API Key real
genai.configure(api_key="AIzaSyD4U1zKzkhMJzmMCJ79dIApR9EiHNcwatQ")
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Asistente Ventas", layout="centered", page_icon="📊")

# 2. CARGA Y LIMPIEZA DE DATOS (Optimizado para el CSV específico)
@st.cache_data
def load_data():
    try:
        # --- CONFIGURACIÓN DRIVE ---
        # PEGA AQUÍ TU ID DE ARCHIVO
        FILE_ID = "16HQlKYZavkZucbJQqLc4pHcwdK-ONH5wv-xWbEC4NTE" 
        
        # URL de descarga directa para Pandas
        drive_url = f'https://docs.google.com/spreadsheets/d/16HQlKYZavkZucbJQqLc4pHcwdK-ONH5wv-xWbEC4NTE/edit?usp=sharing'
        
        # Cargamos el archivo directamente desde la nube
        df = pd.read_csv(drive_url)
        
        # Limpieza (la misma que ya teníamos para que no falle)
        df.columns = df.columns.str.strip()
        cols_validas = ['Fecha', 'Tienda', 'Producto', 'Categoria', 'Cantidad', 'Precio_Unitario', 'Total']
        df = df[cols_validas]
        
        df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
        df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Drive: {e}")
        return None

df = load_data()

# 3. INTERFAZ DE USUARIO
st.title("📊 Mi Asistente de Ventas")
st.markdown("Consulta tus datos de ventas en lenguaje natural.")

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. LÓGICA DEL CHAT
if prompt := st.chat_input("¿Qué quieres saber hoy?"):
    # Agregar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.spinner("Analizando base de datos..."):
        # Instrucción estricta para la IA
        sys_prompt = f"""
        Actúa como un programador senior de Python y experto en Pandas.
        Tienes un DataFrame 'df' con estas columnas: {df.columns.tolist()}
        
        REGLAS:
        1. Responde ÚNICAMENTE con código funcional de Python.
        2. No incluyas explicaciones, ni bloques de texto, ni '```python'.
        3. El resultado final DEBE guardarse en una variable llamada 'resultado'.
        4. Si el usuario pide un listado o top, usa .head(10).
        
        Pregunta: {prompt}
        """

        try:
            # Obtener respuesta de Gemini
            raw_response = model.generate_content(sys_prompt).text
            
            # Limpiar el código por si la IA agregó markdown
            codigo = raw_response.replace('```python', '').replace('```', '').strip()
            
            # Ejecutar el código en un entorno controlado
            loc = {'df': df, 'pd': pd}
            exec(codigo, {}, loc)
            
            # Obtener el resultado (con Plan B por si la IA no usó el nombre 'resultado')
            resultado = loc.get('resultado')
            if resultado is None:
                vars_creadas = [v for k, v in loc.items() if k not in ['df', 'pd']]
                resultado = vars_creadas[-1] if vars_creadas else "No se pudo calcular."

            # Mostrar respuesta en la interfaz
            with st.chat_message("assistant"):
                container = st.container()
                
                if isinstance(resultado, (pd.DataFrame, pd.Series)):
                    container.write("Resultados encontrados:")
                    container.dataframe(resultado, use_container_width=True)
                else:
                    # Si es un número, mostrarlo como métrica
                    if isinstance(resultado, (int, float)):
                        container.metric("Valor Calculado", f"${resultado:,.2f}")
                    else:
                        container.info(f"Resultado: {resultado}")

                # Explicación humana de la IA
                res_humano = model.generate_content(f"Explica brevemente este dato de ventas: {resultado} para la duda: {prompt}")
                container.write(res_humano.text)
                
                # Guardar en historial
                st.session_state.messages.append({"role": "assistant", "content": res_humano.text})

        except Exception as e:
            st.error("No logré procesar esa consulta. Intenta ser más específico.")
            with st.expander("Detalle técnico del error"):
                st.code(codigo)
                st.write(e)