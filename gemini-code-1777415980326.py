import streamlit as st
import pandas as pd
import google.generativeai as genai

# Configuración API
genai.configure(api_key="TU_API_KEY_AQUI")
model = genai.GenerativeModel('gemini-1.5-flash')

@st.cache_data
def load_data():
    # 1. Leemos solo las columnas que nos importan para evitar la basura del Excel
    columnas_reales = ['Fecha', 'Tienda', 'Producto', 'Categoria', 'Cantidad', 'Precio_Unitario', 'Total']
    df = pd.read_csv("Ventas Asistente - Ventas.csv", usecols=columnas_reales)
    
    # 2. Limpieza de datos: Convertir a números (por si vienen con basura)
    df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
    df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    
    return df

df = load_data()

# Interfaz simplificada para móvil
st.title("📊 Mi Asistente de Ventas")

if prompt := st.chat_input("¿Qué quieres consultar?"):
    with st.chat_message("user"):
        st.write(prompt)

    with st.spinner("Calculando..."):
        # PROMPT DE INGENIERÍA: Forzamos a la IA a ser un robot de código
        sys_prompt = f"""
        Actúa como un experto en Python y Pandas.
        Datos: DataFrame 'df' con columnas: {df.columns.tolist()}
        
        REGLA DE ORO: Responde ÚNICAMENTE con el código Python. 
        No digas "Aquí tienes", no uses bloques ```. Solo código.
        El resultado debe ser una variable llamada 'resultado'.
        
        Pregunta del usuario: {prompt}
        """
        
        try:
            response = model.generate_content(sys_prompt)
            # Limpieza extrema del texto recibido
            codigo_limpio = response.text.replace('```python', '').replace('```', '').strip()
            # Si la IA escribió texto antes del código, lo ignoramos
            lineas = [l for l in codigo_limpio.split('\n') if '=' in l or '.' in l]
            codigo_final = '\n'.join(lineas)

            # Diccionario de ejecución
            scope = {'df': df, 'pd': pd}
            exec(codigo_final, scope)
            resultado = scope.get('resultado')

            with st.chat_message("assistant"):
                if isinstance(resultado, (pd.DataFrame, pd.Series)):
                    st.table(resultado)
                else:
                    st.metric("Resultado", f"{resultado}")
                
                # Explicación humana opcional
                explicacion = model.generate_content(f"Explica este resultado: {resultado} para la duda: {prompt}")
                st.write(explicacion.text)

        except Exception as e:
            st.error("No pude procesar la duda. Prueba preguntando algo más simple.")
            st.info("La IA intentó ejecutar esto:")
            st.code(codigo_final)