import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Consolidador y Filtro de CSVs",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Unificador de CSVs y Buscador por Student ID")
st.write("Sube tus archivos CSV para unificarlos y consultar la información de cualquier cliente/estudiante.")

# Sidebar para cargar archivos y configurar la combinación
st.sidebar.header("1. Cargar Archivos CSV")
uploaded_files = st.sidebar.file_uploader(
    "Selecciona uno o varios archivos CSV", 
    type=["csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    dfs = []
    file_names = []
    
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
            file_names.append(file.name)
        except Exception as e:
            st.error(f"Error al leer {file.name}: {e}")

    st.sidebar.success(f"Cargados {len(dfs)} archivo(s): {', '.join(file_names)}")

    st.sidebar.header("2. Método de Combinación")
    merge_method = st.sidebar.radio(
        "¿Cómo deseas mezclar las tablas?",
        ("Combinar por columna 'student_id' (Merge/Join)", 
         "Apilar filas de tablas similares (Concat)"),
        help="Elige 'Merge' si tienes tablas distintas. Elige 'Concat' si son archivos con la misma estructura."
    )

    merged_df = None

    if merge_method == "Combinar por columna 'student_id' (Merge/Join)":
        valid_dfs = [df for df in dfs if "student_id" in df.columns]
        
        if len(valid_dfs) < len(dfs):
            st.warning("Algunos archivos no contienen la columna 'student_id'. Solo se procesarán los que sí la tienen.")
        
        if valid_dfs:
            merged_df = valid_dfs[0]
            for i, df in enumerate(valid_dfs[1:], start=1):
                merged_df = pd.merge(merged_df, df, on="student_id", how="outer", suffixes=('', f'_doc{i}'))
        else:
            st.error("Ninguno de los archivos contiene la columna 'student_id'.")
    else:
        merged_df = pd.concat(dfs, ignore_index=True)

    if merged_df is not None and not merged_df.empty:
        st.subheader("📋 Vista Previa de los Datos Unificados")
        st.write(f"Total de registros: **{len(merged_df):,}** | Total de columnas: **{len(merged_df.columns)}**")
        st.dataframe(merged_df.head(10), use_container_width=True)

        # --- SECCIÓN DE FILTROS ---
        st.markdown("---")
        st.subheader("🔍 Filtros Activos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**👤 Filtro por `student_id`**")
            if "student_id" in merged_df.columns:
                unique_ids = merged_df["student_id"].dropna().astype(str).unique().tolist()
                selected_id = st.selectbox("Selecciona el ID:", options=["-- Todos / Ninguno en específico --"] + unique_ids)
                text_search = st.text_input("O busca un ID por texto parcial:")
            else:
                selected_id = "-- Todos / Ninguno en específico --"
                text_search = ""
                st.warning("La columna 'student_id' no está presente.")

        with col2:
            st.markdown("**🎂 Filtro por Grupo/Edad**")
            possible_age_cols = [c for c in merged_df.columns if any(k in c.lower() for k in ["edad", "age", "grupo", "range", "bucket"])]
            selected_age_col = st.selectbox("Selecciona la columna a filtrar:", options=["Ninguna"] + possible_age_cols + list(merged_df.columns))
            
            selected_age_groups = []
            if selected_age_col != "Ninguna":
                unique_ages = merged_df[selected_age_col].dropna().unique().tolist()
                selected_age_groups = st.multiselect("Selecciona el/los grupo(s):", options=unique_ages)

        filtered_df = merged_df.copy()

        if "student_id" in filtered_df.columns:
            if selected_id != "-- Todos / Ninguno en específico --":
                filtered_df = filtered_df[filtered_df["student_id"].astype(str) == selected_id]
            elif text_search:
                filtered_df = filtered_df[filtered_df["student_id"].astype(str).str.contains(text_search, case=False, na=False)]
        
        if selected_age_col != "Ninguna" and selected_age_groups:
            filtered_df = filtered_df[filtered_df[selected_age_col].isin(selected_age_groups)]

        # --- LÓGICA DE PUNTOS EN LA TABLA CONSOLIDADA ---
        totalmount_cols = [c for c in filtered_df.columns if "totalmount" in c.lower()]
        if totalmount_cols:
            col_name = totalmount_cols[0]
            # Crear la columna de puntos por cada fila
            filtered_df["puntos_calculados"] = pd.to_numeric(filtered_df[col_name], errors='coerce').fillna(0)
            total_puntos_global = filtered_df["puntos_calculados"].sum()

        st.write(f"Resultados consolidados encontrados: **{len(filtered_df)}**")
        
        if totalmount_cols:
            st.success(f"🏆 **Total de puntos acumulados en esta selección (1€ = 1 Pto): {total_puntos_global:,.2f}**")

        st.dataframe(filtered_df, use_container_width=True)

        # --- SECCIÓN: TABLAS INDIVIDUALES FILTRADAS ---
        st.markdown("---")
        st.subheader("📑 Resultados Desglosados en los Archivos Originales")
        
        for file_name, raw_df in zip(file_names, dfs):
            temp_df = raw_df.copy()
            
            if selected_id != "-- Todos / Ninguno en específico --" or text_search:
                if "student_id" in temp_df.columns:
                    if selected_id != "-- Todos / Ninguno en específico --":
                        temp_df = temp_df[temp_df["student_id"].astype(str) == selected_id]
                    elif text_search:
                        temp_df = temp_df[temp_df["student_id"].astype(str).str.contains(text_search, case=False, na=False)]
                else:
                    temp_df = temp_df.iloc[0:0] 
            
            if selected_age_col != "Ninguna" and selected_age_groups:
                if selected_age_col in temp_df.columns:
                    temp_df = temp_df[temp_df[selected_age_col].isin(selected_age_groups)]
                else:
                    temp_df = temp_df.iloc[0:0]
            
            # --- LÓGICA DE PUNTOS EN VENTAS.CSV ---
            if "ventas" in file_name.lower() and "totalmount" in temp_df.columns.str.lower():
                # Encontrar el nombre exacto de la columna respetando mayúsculas/minúsculas
                col_exacta = [c for c in temp_df.columns if c.lower() == "totalmount"][0]
                temp_df["puntos_calculados"] = pd.to_numeric(temp_df[col_exacta], errors='coerce').fillna(0)
                suma_puntos = temp_df["puntos_calculados"].sum()

            st.markdown(f"**Archivo de origen: `{file_name}`**")
            if len(temp_df) > 0:
                st.write(f"Coincidencias en este archivo: **{len(temp_df)}**")
                
                # Mostrar el cuadro de éxito si es el archivo de ventas
                if "ventas" in file_name.lower() and "totalmount" in temp_df.columns.str.lower():
                    st.success(f"🏆 Puntos generados en `{file_name}`: **{suma_puntos:,.2f}**")
                    
                st.dataframe(temp_df, use_container_width=True)
            else:
                st.info("Sin coincidencias (o la tabla no contiene las columnas filtradas).")

        # --- DESCARGAS ---
        st.markdown("---")
        st.subheader("📥 Descargar Resultados Consolidados")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            csv_all = merged_df.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar Tabla Completa Unificada (CSV)", data=csv_all, file_name="clientes_unificados.csv", mime="text/csv")
        with col_d2:
            csv_filtered = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar Solo Datos Filtrados (CSV)", data=csv_filtered, file_name="cliente_filtrado.csv", mime="text/csv")
else:
    st.info("👆 Por favor, sube uno o más archivos CSV desde la barra lateral para empezar.")
