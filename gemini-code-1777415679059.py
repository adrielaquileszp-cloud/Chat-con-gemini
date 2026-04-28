import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. Configuración
genai.configure(api_key="TU_API_KEY_AQUI")
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Asistente de Ventas", layout="centered")
st.title("📊 Asistente de Ventas Pro")

@st.cache_data
def load_data():
    # Cargamos el CSV y limpiamos nombres de columnas
    df = pd.read_csv("Ventas Asistente - Ventas.csv")
    df.columns = df.columns.str.strip() # Quita espacios vacíos
    return df

df = load_data()

# 2. El "Sistema" de la IA
# Le explicamos a Gemini qué columnas tiene el archivo para que sepa qué filtrar
contexto_columnas = f"""
Tienes un DataFrame llamado 'df' con las siguientes columnas:
{df.columns.tolist()}
- Tienda: Nombres de las sucursales.
- Producto: Nombre del artículo.
- Total: Monto de la venta.
- Cantidad: Unidades vendidas.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ej: ¿Cuál es la tienda que más vende?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. Lógica de razonamiento
    with st.spinner("Analizando datos..."):
        try:
            # Le pedimos a Gemini que genere la instrucción de Pandas
            instruccion_ia = model.generate_content(f"""
            {contexto_columnas}
            Usuario pregunta: {prompt}
            Genera SOLO UNA LINEA de código Python usando pandas para obtener la respuesta. 
            El resultado debe guardarse en una variable llamada 'resultado'.
            Ejemplo: resultado = df.groupby('Tienda')['Total'].sum().nlargest(1)
            """)
            
            # Ejecutamos el código generado por la IA de forma segura
            codigo = instruccion_ia.text.replace('```python', '').replace('```', '').strip()
            local_vars = {'df': df}
            exec(codigo, {}, local_vars)
            resultado_final = local_vars.get('resultado', 'No se pudo calcular')

            # 4. Respuesta final
            respuesta_humana = model.generate_content(f"El usuario preguntó: {prompt}. El resultado del cálculo fue: {resultado_final}. Explícalo de forma breve y profesional.")
            
            with st.chat_message("assistant"):
                st.markdown(respuesta_humana.text)
                # Opcional: mostrar la tabla del resultado si es un dataframe
                if isinstance(resultado_final, (pd.DataFrame, pd.Series)):
                    st.dataframe(resultado_final)
                
                st.session_state.messages.append({"role": "assistant", "content": respuesta_humana.text})

        except Exception as e:
            st.error(f"Ups, tuve un problema con ese cálculo. Intenta ser más específico. Error: {e}")