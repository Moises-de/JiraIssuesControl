import streamlit as st
import pandas as pd
import re

st.markdown("<h1 style='color:#0030f6'>📊 Reporte de estimaciones por usuario</h1>", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Sube tu archivo Excel (ej: worklogs_2025-03-29_2025-04-29)", 
    type=["xlsx"]
)

if uploaded_file is not None:
    try:
        # Extraer fechas desde el nombre del archivo
        filename = uploaded_file.name
        match = re.search(r'worklogs?_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})', filename)
        if not match:
            st.error("⚠️ El nombre del archivo no contiene las fechas esperadas.")
        else:
            start_str, end_str = match.groups()
            start_date = pd.to_datetime(start_str).date()
            end_date = pd.to_datetime(end_str).date()

            # Generar días hábiles
            business_days = pd.bdate_range(start=start_date, end=end_date).date

            # Leer archivo y preparar
            df = pd.read_excel(uploaded_file)
            required_columns = ['Issue Key', 'Time Spent', 'Time Spent (seconds)', 'Author', 'Start Date', 'Project Key']
            df = df[required_columns]
            df['Start Date'] = pd.to_datetime(df['Start Date']).dt.date
            df['Time Spent (hours)'] = df['Time Spent (seconds)'] / 3600

            # Agrupación
            df_grouped = df.groupby(['Author', 'Start Date'], as_index=False)['Time Spent (hours)'].sum()

            # Autores únicos
            authors = df_grouped['Author'].unique()

            # Todos los pares posibles Autor x Día
            complete_index = pd.MultiIndex.from_product([authors, business_days], names=['Author', 'Start Date'])
            df_complete = pd.DataFrame(index=complete_index).reset_index()

            # Unir con datos reales
            df_final = pd.merge(df_complete, df_grouped, on=['Author', 'Start Date'], how='left')
            df_final['Time Spent (hours)'] = df_final['Time Spent (hours)'].fillna(0)

            # Evaluación con emoji
            def evaluar(horas):
                if horas == 0:
                    return "❌ No estimó"
                elif horas < 8:
                    return "⚠️ Incumple estimativo"
                elif horas == 8:
                    return "✅ Cumple estimativo"
                else:
                    return "🚀 Excede estimativo"

            df_final['Evaluación'] = df_final['Time Spent (hours)'].apply(evaluar)

            # Filtro visual con estilo
            st.markdown("<h4 style='color:#f15a30'>Filtrar por autor</h4>", unsafe_allow_html=True)
            selected_author = st.selectbox("", options=["Todos"] + list(authors))

            if selected_author != "Todos":
                df_filtered = df_final[df_final['Author'] == selected_author]
            else:
                df_filtered = df_final

            # Mostrar resultados
            st.markdown("<h4 style='color:#f15a30'>Resumen de estimaciones</h4>", unsafe_allow_html=True)
            st.dataframe(df_filtered.sort_values(by=['Author', 'Start Date']))

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
