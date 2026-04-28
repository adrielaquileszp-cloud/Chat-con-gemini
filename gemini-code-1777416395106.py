@st.cache_data
def load_data():
    # Cargamos el archivo sin filtrar columnas primero
    df = pd.read_csv("Ventas Asistente - Ventas.csv")
    
    # LIMPIEZA CRUCIAL:
    # 1. Quitamos espacios en blanco al inicio/final de los nombres de columnas
    df.columns = df.columns.str.strip()
    
    # 2. Eliminamos columnas que no tengan nombre o sean 'Unnamed'
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # 3. Solo nos quedamos con las que nos sirven (asegurando que existan)
    cols_interes = ['Fecha', 'Tienda', 'Producto', 'Categoria', 'Cantidad', 'Precio_Unitario', 'Total']
    df = df[cols_interes]
    
    # 4. Limpieza de tipos
    df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
    df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    
    return df

# ... (resto del código del chat)

    # En el bloque del exec, asegúrate de que el prompt sea así:
    sys_prompt = f"""
    Eres un experto en Python. Solo responde con CÓDIGO.
    Dataframe 'df' con columnas: {df.columns.tolist()}
    Pregunta: {prompt}
    Importante: El resultado final DEBE estar en la variable 'resultado'.
    Si es una suma de la columna Total, usa: resultado = df['Total'].sum()
    """