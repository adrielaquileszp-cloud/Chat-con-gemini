import streamlit as st
import pandas as pd
import google.generativeai as genai
import re

# Configuración
genai.configure(api_key="TU_API_KEY_AQUI")
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Asistente Ventas", layout="centered")

@st.cache_data
def load_data():
    # Cargamos solo las columnas necesarias y limpiamos
    df = pd.read_csv("Ventas Asistente - Ventas.csv", usecols=['Fecha', 'Tienda', 'Producto', 'Categoria', 'Cantidad', 'Precio_Unitario', 'Total'])
    df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    return df

df = load_data()

st.title("📊 Consultas de Ventas")

if prompt := st.chat_input("¿Qué quieres saber?"):
    with st.chat_message("user"):
        st.write(prompt)

    # El Prompt ahora es súper estricto
    sys_prompt = f"""
    Eres un experto en Python. Solo puedes responder con CÓDIGO.
    Dataframe 'df' con columnas: {df.columns.tolist()}
    Pregunta: {prompt}
    Instrucción: Calcula lo solicitado y guarda el resultado final en la variable 'resultado'.
    No escribas NADA que no sea código.
    """

    try:
        response = model.generate_content(sys_prompt).text
        
        # --- EXTRACCIÓN QUIRÚRGICA ---
        # Buscamos cualquier cosa que esté entre bloques de código o simplemente limpiamos
        codigo = response.replace('```python', '').replace('```', '').strip()
        
        # Creamos un diccionario para capturar el resultado
        loc = {'df': df, 'pd': pd}
        exec(codigo, {}, loc)
        
        # Si la IA no usó 'resultado', buscamos cualquier variable nueva
        resultado = loc.get('resultado')
        if resultado is None:
            # Plan B: tomar la última variable creada en el diccionario
            vars_creadas = [v for k, v in loc.items() if k not in ['df', 'pd']]
            resultado = vars_creadas[-1] if vars_creadas else "No se pudo calcular"

        with st.chat_message("assistant"):
            if isinstance(resultado, (pd.DataFrame, pd.Series)):
                st.write("Aquí tienes los datos:")
                st.dataframe(resultado)
            else:
                st.metric("Resultado final", f"{resultado}")
            
            # Explicación breve
            exp = model.generate_content(f"Resume este dato en una frase para el jefe: {resultado}")
            st.write(exp.text)

    except Exception as e:
        st.error("Hubo un detalle técnico. Intenta preguntar diferente.")
        with st.expander("Ver error técnico"):
            st.code(codigo)
            st.write(e)