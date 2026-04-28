# 3. Lógica de razonamiento mejorada
    with st.spinner("Analizando datos..."):
        try:
            # Pedimos el código con instrucciones más rígidas
            prompt_ia = f"""
            {contexto_columnas}
            Usuario pregunta: {prompt}
            Genera código Python usando la librería pandas para responder.
            REGLAS ESTRICTAS:
            1. Solo responde con el código, sin texto adicional, sin '```python'.
            2. El resultado final DEBE guardarse en una variable llamada 'resultado'.
            3. Si es un ranking, usa .head() o .nlargest().
            """
            
            instruccion_ia = model.generate_content(prompt_ia)
            codigo_sucio = instruccion_ia.text
            
            # --- LIMPIEZA DE CÓDIGO ---
            # Eliminamos posibles bloques de markdown que la IA suele poner
            codigo_limpio = codigo_sucio.replace('```python', '').replace('```', '').strip()
            # Quitamos cualquier línea que no parezca código (comentarios de la IA)
            lineas = [line para line in codigo_limpio.split('\n') if not line.startswith(('Aquí', 'Este', 'Sure', 'Claro'))]
            codigo_final = '\n'.join(lineas)
            
            # Ejecución
            local_vars = {'df': df, 'pd': pd}
            exec(codigo_final, {}, local_vars)
            resultado_final = local_vars.get('resultado', 'No se pudo generar un resultado.')

            # 4. Respuesta humana
            res_ia = model.generate_content(f"Pregunta: {prompt}. Resultado numérico: {resultado_final}. Resume el hallazgo en una frase corta.")
            
            with st.chat_message("assistant"):
                st.write(res_ia.text)
                if isinstance(resultado_final, (pd.DataFrame, pd.Series)):
                    st.table(resultado_final) # st.table se ve mejor en móvil que st.dataframe
                else:
                    st.info(f"Valor calculado: {resultado_final}")
                
                st.session_state.messages.append({"role": "assistant", "content": res_ia.text})

        except Exception as e:
            st.error(f"Hubo un error al procesar el código. Intenta preguntar de otra forma.")
            st.code(codigo_final) # Esto te servirá para ver qué intentó escribir la IA