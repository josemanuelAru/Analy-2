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
        st.write("Consolida los datos clave para defender tus 3 diapositivas de la **Clase 1** (Perfilado y Selección de Segmentos) y **Clase 2** (Evaluación de Canales y Experimento).")

        # Verificar tablas mínimas necesarias
        has_clientes = any("clientes" in name.lower() and "details" not in name.lower() for name in dfs.keys())
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
            has_details = len(details_file) > 0
            if has_details:
                df_details = dfs[details_file[0]]
                cols_to_use = [c for c in df_details.columns if c not in merged_data.columns or c == 'student_id']
                merged_data = pd.merge(merged_data, df_details[cols_to_use], on='student_id', how='left')

            # Normalizar nombre de la columna bucket_name tras los cruces
            bucket_col = [c for c in merged_data.columns if 'bucket_name' in c][0]

            # --- SECCIÓN 1: COMPARATIVA GLOBAL DE SEGMENTOS ---
            st.subheader("1. Visión General de los 11 Segmentos RFM")
            
            segment_table = merged_data.groupby(bucket_col).agg(
                usuarios=('student_id', 'count'),
                gasto_total_eur=('gasto_total', 'sum'),
                ticket_medio_eur=('ticket_medio', 'mean'),
                frecuencia_media=('frecuencia', 'mean')
            ).reset_index()

            segment_table.rename(columns={bucket_col: 'Segmento'}, inplace=True)
            segment_table['ticket_medio_eur'] = segment_table['ticket_medio_eur'].round(2)
            segment_table['frecuencia_media'] = segment_table['frecuencia_media'].round(1)
            segment_table['gasto_total_eur'] = segment_table['gasto_total_eur'].round(2)

            st.dataframe(segment_table.sort_values(by='gasto_total_eur', ascending=False), use_container_width=True)

            # --- SECCIÓN 2: DEFENSA DE LOS 3 SEGMENTOS SELECCIONADOS ---
            st.markdown("---")
            st.subheader("2. Ficha de Defensa: Tus 3 Segmentos Prioritarios")

            target_segments = ['1. Champions', '2. Loyal Active', '6. At Risk']
            df_targets = merged_data[merged_data[bucket_col].isin(target_segments)]

            col1, col2, col3 = st.columns(3)

            for idx, (col, seg) in enumerate(zip([col1, col2, col3], target_segments)):
                df_seg = df_targets[df_targets[bucket_col] == seg]
                with col:
                    st.markdown(f"### `{seg}`")
                    st.metric("Usuarios Únicos", f"{len(df_seg):,}")
                    st.metric("Ticket Medio", f"{df_seg['ticket_medio'].mean():.2f} €")
                    st.metric("Frecuencia Anual", f"{df_seg['frecuencia'].mean():.1f} visitas")
                    st.metric("Gasto Total Acumulado", f"{df_seg['gasto_total'].sum():,.2f} €")

                    if 'points_balance' in df_seg.columns:
                        st.write(f"🏅 **Puntos acumulados (media):** {df_seg['points_balance'].mean():,.0f} pts")
                    if 'push_optin' in df_seg.columns:
                        st.write(f"📲 **Aceptan Notificaciones Push:** {df_seg['push_optin'].mean()*100:.1f}%")

            # --- SECCIÓN 3: PERFIL DEMOGRÁFICO ---
            st.markdown("---")
            st.subheader("3. Perfil Demográfico (`persona`) de los Segmentos Prioritarios")

            if not has_details:
                st.info("ℹ️ Sube el archivo `Customers_details.csv` en la barra lateral para desbloquear el desglose por tipo de Persona.")
            else:
                st.markdown("#### 👤 Perfil Predominante (`persona`) por Segmento")
                persona_summary = df_targets.groupby([bucket_col, 'persona'])['student_id'].count().unstack().fillna(0)
                persona_pct = persona_summary.div(persona_summary.sum(axis=1), axis=0) * 100
                st.dataframe(persona_pct.round(1).astype(str) + " %", use_container_width=True)

            # --- SECCIÓN 4: ENGAGEMENT POR FIDELIZACIÓN INTERACTIVO ---
            st.markdown("---")
            st.subheader("4. Nivel de Engagement por Fidelización (11 Segmentos)")

            if not has_details:
                st.info("ℹ️ Carga `Customers_details.csv` para ver las métricas completas de lealtad de los 11 segmentos.")
            else:
                redeemer_cols_all = [c for c in merged_data.columns if 'redeemer_' in c]
                merged_data['total_canjes_familias'] = merged_data[redeemer_cols_all].sum(axis=1)

                loyalty_engagement = merged_data.groupby(bucket_col).agg(
                    pct_usuarios_que_canjean=('points_burned', lambda x: (x < 0).mean() * 100),
                    puntos_ganados_media=('points_earned', 'mean'),
                    puntos_canjeados_media=('points_burned', 'mean'),
                    saldo_puntos_media=('points_balance', 'mean'),
                    familias_productos_canjeadas=('total_canjes_familias', 'mean')
                ).reset_index()

                loyalty_engagement.rename(columns={bucket_col: 'Segmento'}, inplace=True)
                
                # Crear versión visual formateada de la tabla
                loyalty_display = loyalty_engagement.copy()
                loyalty_display['pct_usuarios_que_canjean'] = loyalty_display['pct_usuarios_que_canjean'].round(1).astype(str) + " %"
                loyalty_display['puntos_ganados_media'] = loyalty_display['puntos_ganados_media'].round(0)
                loyalty_display['puntos_canjeados_media'] = loyalty_display['puntos_canjeados_media'].round(0)
                loyalty_display['saldo_puntos_media'] = loyalty_display['saldo_puntos_media'].round(0)
                loyalty_display['familias_productos_canjeadas'] = loyalty_display['familias_productos_canjeadas'].round(2)

                st.dataframe(loyalty_display, use_container_width=True)

                # --- SELECTOR INTERACTIVO Y DESGLOSE DE PRODUCTOS ---
                st.markdown("### 🍟 Top Productos Canjeados por Segmento")
                all_segments = sorted(merged_data[bucket_col].dropna().unique().tolist())
                
                selected_segment = st.selectbox(
                    "Selecciona un segmento para ver sus productos más canjeados:",
                    options=all_segments
                )

                if selected_segment and redeemer_cols_all:
                    df_selected_seg = merged_data[merged_data[bucket_col] == selected_segment]
                    
                    # Calcular porcentaje de canje por producto en el segmento seleccionado
                    product_redemptions = (df_selected_seg[redeemer_cols_all].mean() * 100).round(1).reset_index()
                    product_redemptions.columns = ['Producto', 'Porcentaje de Canje (%)']
                    product_redemptions['Producto'] = product_redemptions['Producto'].str.replace('redeemer_', '').str.capitalize()
                    
                    # Ordenar de mayor a menor
                    product_redemptions = product_redemptions.sort_values(by='Porcentaje de Canje (%)', ascending=False).reset_index(drop=True)

                    col_table, col_chart = st.columns([1, 1])

                    with col_table:
                        st.markdown(f"**Ranking de Canjes en `{selected_segment}`:**")
                        st.dataframe(product_redemptions, use_container_width=True)

                    with col_chart:
                        st.markdown(f"**Gráfico de Canjes en `{selected_segment}`:**")
                        st.bar_chart(product_redemptions.set_index('Producto'))

            # --- SECCIÓN 5: ESTRATEGIA Y RECOMENDACIÓN DE NEGOCIO ---
            st.markdown("---")
            st.subheader("5. Argumentario de Negocio para la Presentación (3 Diapositivas)")
            
            st.markdown("""
            * **Diapositiva 1: Protegemos a la cúspide (`1. Champions`)**
                * *Diagnóstico:* 7.516 usuarios inyectan 2,71 M€ (24,7 compras/año). Dominados por **Engaged Family Member (39,0%)**. Tienen un engagement récord (**98,7% utiliza sus puntos**).
                * *Acción:* Cero descuentos directos. Campañas de aceleración de puntos acumulados (`points_balance` ~991 pts) enfocadas en sus canjes favoritos: **Big Mac (14,2%)** y **McNuggets (13,4%)**.
            * **Diapositiva 2: Escalamos la clase media (`2. Loyal Active`)**
                * *Diagnóstico:* 5.058 usuarios con el mismo ticket medio (14,27 €) pero la mitad de frecuencia (12,7 compras/año). Engagement muy alto en lealtad (**94,4% de penetración**).
                * *Acción:* Retos condicionados por Push (45,7% opt-in) para aumentar visitas consecutivas premiando con **Big Mac (13,3%)** o **Patatas Fritas (8,0%)**.
            * **Diapositiva 3: Retención urgente (`6. At Risk`)**
                * *Diagnóstico:* 6.960 usuarios en enfriamiento (488k € en riesgo de fuga). Su penetración de lealtad ha caído al **62,3%** y el algoritmo los mueve a **Non Transactional Users (22,8%)**.
                * *Acción:* Campañas agresivas de *Winback* con cupones (*Deals*) de tiempo limitado vía Push/Email antes de que caigan al segmento *Hibernating*.
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
