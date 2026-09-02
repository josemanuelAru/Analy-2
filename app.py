import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="McDonald's NL - CRM Analytics & Caso Práctico",
    page_icon="🍔",
    layout="wide"
)

st.title("🍔 McDonald's NL — CRM & Customer Analytics Dashboard")
st.write("Carga tus archivos CSV del caso práctico (`clientes.csv`, `ventas.csv`, `Customers_details.csv`, `Campañas.csv`, etc.) para realizar el análisis interactivo.")

# Sidebar: Carga de archivos
st.sidebar.header("1. Cargar Archivos CSV")
uploaded_files = st.sidebar.file_uploader(
    "Selecciona los archivos CSV del proyecto", 
    type=["csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    dfs = {}
    for file in uploaded_files:
        try:
            dfs[file.name] = pd.read_csv(file)
        except Exception as e:
            st.error(f"Error al cargar {file.name}: {e}")

    st.sidebar.success(f"Cargados {len(dfs)} archivo(s)")

    # Modos de navegación
    mode = st.sidebar.radio(
        "Modo de Navegación:",
        ("📊 Módulo Caso Práctico (Clase 1 & 2)", "📂 Tablas Individuales y Búsqueda")
    )

    if mode == "📊 Módulo Caso Práctico (Clase 1 & 2)":
        st.header("🎯 Módulo de Trabajo: Caso Práctico CRM")
        st.write("Este módulo consolida los datos clave para defender tus 3 diapositivas de la **Clase 1** (Perfilado y Selección de Segmentos) y **Clase 2** (Evaluación de Canales y Experimento).")

        # Verificar tablas mínimas necesarias
        has_clientes = any("clientes" in name.lower() for name in dfs.keys())
        has_ventas = any("ventas" in name.lower() for name in dfs.keys())

        if not (has_clientes and has_ventas):
            st.warning("⚠️ Para usar este módulo necesitas cargar al menos los archivos `clientes.csv` y `ventas.csv`.")
        else:
            # Obtener dataframes principales
            clientes_file = [name for name in dfs.keys() if "clientes" in name.lower() and "details" not in name.lower()][0]
            ventas_file = [name for name in dfs.keys() if "ventas" in name.lower()][0]

            df_clientes = dfs[clientes_file]
            df_ventas = dfs[ventas_file]

            # Cruce de ventas con clientes por student_id
            sales_summary = df_ventas.groupby('student_id').agg(
                gasto_total=('totalamount', 'sum'),
                frecuencia=('sale_id', 'nunique'),
                ticket_medio=('totalamount', 'mean')
            ).reset_index()

            merged_data = pd.merge(df_clientes, sales_summary, on='student_id', how='left')

            # Si está cargado Customers_details.csv, lo unimos
            details_file = [name for name in dfs.keys() if "details" in name.lower()]
            if details_file:
                df_details = dfs[details_file[0]]
                cols_to_use = [c for c in df_details.columns if c not in merged_data.columns or c == 'student_id']
                merged_data = pd.merge(merged_data, df_details[cols_to_use], on='student_id', how='left')

            # --- SECCIÓN 1: COMPARATIVA GLOBAL DE SEGMENTOS ---
            st.subheader("1. Visión General de los 11 Segmentos RFM")
            
            segment_table = merged_data.groupby('bucket_name').agg(
                usuarios=('student_id', 'count'),
                gasto_total_eur=('gasto_total', 'sum'),
                ticket_medio_eur=('ticket_medio', 'mean'),
                frecuencia_media=('frecuencia', 'mean')
            ).reset_index()

            segment_table['ticket_medio_eur'] = segment_table['ticket_medio_eur'].round(2)
            segment_table['frecuencia_media'] = segment_table['frecuencia_media'].round(1)
            segment_table['gasto_total_eur'] = segment_table['gasto_total_eur'].round(2)

            st.dataframe(segment_table.sort_values(by='gasto_total_eur', ascending=False), use_container_width=True)

            # --- SECCIÓN 2: DEFENSA DE LOS 3 SEGMENTOS SELECCIONADOS ---
            st.markdown("---")
            st.subheader("2. Ficha de Defensa: Tus 3 Segmentos Prioritarios (Clase 1)")

            target_segments = ['1. Champions', '2. Loyal Active', '6. At Risk']
            df_targets = merged_data[merged_data['bucket_name'].isin(target_segments)]

            col1, col2, col3 = st.columns(3)

            for idx, (col, seg) in enumerate(zip([col1, col2, col3], target_segments)):
                df_seg = df_targets[df_targets['bucket_name'] == seg]
                with col:
                    st.markdown(f"### `{seg}`")
                    st.metric("Usuarios Únicos", f"{len(df_seg):,}")
                    st.metric("Ticket Medio", f"{df_seg['ticket_medio'].mean():.2f} €")
                    st.metric("Frecuencia Anual", f"{df_seg['frecuencia'].mean():.1f} visitas")
                    st.metric("Gasto Total Acumulado", f"{df_seg['gasto_total'].sum():,.2f} €")

                    if 'points_balance' in df_seg.columns:
                        st.write(f"🏅 **Puntos acumulados (media):** {df_seg['points_balance'].mean():,.0f} pts")
                    if 'persona' in df_seg.columns:
                        top_persona = df_seg['persona'].value_counts().index[0] if not df_seg['persona'].dropna().empty else "N/D"
                        st.write(f"👤 **Persona dominante:** {top_persona}")
                    if 'push_optin' in df_seg.columns:
                        st.write(f"📲 **Aceptan Notificaciones Push:** {df_seg['push_optin'].mean()*100:.1f}%")

            # --- SECCIÓN 3: ESTRATEGIA Y RECOMENDACIÓN DE NEGOCIO ---
            st.markdown("---")
            st.subheader("3. Argumentario de Negocio para la Presentación (3 Diapositivas)")
            
            st.markdown("""
            * **Diapositiva 1: Protegemos a la cúspide (`1. Champions`)**
                * *Diagnóstico:* 7.516 usuarios inyectan 2,71 Millones de € (24,7 compras/año).
                * *Acción:* Cero descuentos en dinero. Campañas de canje de puntos acumulados (`points_balance` promedio ~991 pts) para Big Mac y McNuggets.
            * **Diapositiva 2: Escalamos la clase media (`2. Loyal Active`)**
                * *Diagnóstico:* 5.058 usuarios con el mismo ticket medio (14,27 €) pero la mitad de frecuencia que los Champions (12,7 compras/año).
                * *Acción:* Retos condicionados por Push (45,7% de opt-in) para aumentar visitas consecutivas.
            * **Diapositiva 3: Retención urgente (`6. At Risk`)**
                * *Diagnóstico:* 6.960 usuarios en enfriamiento que representan casi 500k € en riesgo de fuga.
                * *Acción:* Campañas agresivas de *Winback* con cupones (*Deals*) por tiempo limitado vía Push/Email antes de que caigan a *Hibernating*.
            """)

    else:
        # --- MODO DE TABLAS INDIVIDUALES Y BÚSQUEDA ---
        tab_names = [f"📄 {name}" for name in dfs.keys()] + ["🔍 Búsqueda por student_id"]
        tabs = st.tabs(tab_names)

        for i, (file_name, df) in enumerate(dfs.items()):
            with tabs[i]:
                st.subheader(f"Tabla: `{file_name}`")
                st.write(f"Registros: **{len(df):,}** | Columnas: **{len(df.columns)}**")
                st.dataframe(df.head(100), use_container_width=True)

        with tabs[-1]:
            st.subheader("🔍 Filtrar y Buscar Registros por `student_id`")
            
            # Unir todas las tablas que tengan student_id
            valid_dfs = [df for df in dfs.values() if "student_id" in df.columns]
            
            if valid_dfs:
                merged_search = valid_dfs[0]
                for idx, df in enumerate(valid_dfs[1:], start=1):
                    merged_search = pd.merge(merged_search, df, on="student_id", how="outer", suffixes=('', f'_doc{idx}'))

                unique_ids = merged_search["student_id"].dropna().astype(str).unique().tolist()
                selected_id = st.selectbox("Selecciona un `student_id`:", options=["-- Todos --"] + unique_ids)
                text_search = st.text_input("O busca por coincidencia parcial:")

                filtered_search = merged_search.copy()
                if selected_id != "-- Todos --":
                    filtered_search = filtered_search[filtered_search["student_id"].astype(str) == selected_id]
                elif text_search:
                    filtered_search = filtered_search[filtered_search["student_id"].astype(str).str.contains(text_search, case=False, na=False)]

                st.write(f"Resultados encontrados: **{len(filtered_search)}**")
                st.dataframe(filtered_search, use_container_width=True)

                if 'points_balance' in filtered_search.columns:
                    pts = pd.to_numeric(filtered_search['points_balance'], errors='coerce').sum()
                    st.success(f"🏅 **Puntos de lealtad acumulados por la selección:** {pts:,.0f} pts")
            else:
                st.error("No se encontró la columna 'student_id' en los archivos cargados.")
else:
    st.info("👆 Por favor, sube tus archivos CSV desde la barra lateral izquierda para iniciar la herramienta.")
