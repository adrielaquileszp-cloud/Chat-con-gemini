try:
            response = model.generate_content(sys_prompt)
            codigo_limpio = response.text.replace('```python', '').replace('```', '').strip()
            
            # Limpieza: quitamos líneas de texto explicativo
            lineas = [l for l in codigo_limpio.split('\n') if '=' in l or '.' in l]
            
            # --- TRUCO MAESTRO PARA EL ERROR DE 'resultado' ---
            # Si la IA no llamó a la variable 'resultado', vamos a forzarla.
            # Tomamos la última línea de código (que suele ser el resultado final)
            # y la envolvemos para que se asigne a 'resultado'.
            if lineas:
                ultima_linea = lineas[-1]
                if 'resultado =' not in ultima_linea:
                    lineas[-1] = f"resultado = {ultima_linea.split('=')[-1].strip()}"
            
            codigo_final = '\n'.join(lineas)

            # Ejecución con scope controlado
            scope = {'df': df, 'pd': pd}
            exec(codigo_final, scope)
            
            # Buscamos 'resultado', si no existe, buscamos CUALQUIER variable nueva que haya creado la IA
            resultado = scope.get('resultado')
            if resultado is None:
                # Si no hay 'resultado', sacamos el último valor del diccionario que no sea df ni pd
                nuevas_vars = {k: v for k, v in scope.items() if k not in ['df', 'pd', '__builtins__']}
                if nuevas_vars:
                    resultado = list(nuevas_vars.values())[-1]

            with st.chat_message("assistant"):
                if isinstance(resultado, (pd.DataFrame, pd.Series)):
                    st.table(resultado)
                else:
                    st.metric("Resultado", f"{resultado}")
                
                # Explicación humana
                res_final = model.generate_content(f"Explica brevemente este dato de ventas: {resultado}")
                st.write(res_final.text)

        except Exception as e:
            st.error("Error de interpretación. Intenta preguntar algo más directo.")
            st.info("La IA intentó esto:")
            st.code(codigo_final)