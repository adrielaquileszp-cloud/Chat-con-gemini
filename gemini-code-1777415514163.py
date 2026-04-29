import streamlit as st
import pandas as pd
import google.generativeai as genai
import sys

st.title("🔍 Diagnóstico de Sistema")

# 1. Versiones de Software
st.header("1. Versiones")
st.write(f"Python version: {sys.version}")
st.write(f"Streamlit version: {st.__version__}")
st.write(f"Pandas version: {pd.__version__}")

# 2. Verificar API Key y Modelos
st.header("2. Modelos Disponibles")
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    
    modelos = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            modelos.append(m.name)
    
    if modelos:
        st.success("✅ Conexión exitosa con Google AI")
        st.write("Tu API Key tiene acceso a estos modelos:")
        st.write(modelos)
        
        # Guardamos el primero que sirva para recomendarlo después
        st.info(f"Sugerencia: Usa el nombre exacto '{modelos[0]}' en el código.")
    else:
        st.warning("⚠️ Conectó pero no devolvió modelos compatibles.")

except Exception as e:
    st.error("❌ Error de Diagnóstico")
    st.write(e)

# 3. Prueba de lectura de Google Sheets
st.header("3. Prueba de Datos")
try:
    FILE_ID = "16HQlKYZavkZucbJQqLc4pHcwdK-ONH5wv-xWbEC4NTE"
    url = f'https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv'
    test_df = pd.read_csv(url)
    st.success(f"✅ Google Sheets leído correctamente. Filas: {len(test_df)}")
    st.write("Columnas detectadas:", test_df.columns.tolist())
except Exception as e:
    st.error(f"❌ Error al leer Google Sheets: {e}")
