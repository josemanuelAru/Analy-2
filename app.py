import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="McDonald's NL - CRM Analytics & Caso Práctico",
    page_icon="🍔",
    layout="wide"
)

st.title("🍔 McDonald's NL — CRM & Customer Analytics Dashboard")
st.write("Carga tus archivos CSV del caso práctico (`clientes.csv`, `ventas.csv`, `Customers_details.csv`, `Offers.csv`, `Campañas.csv`, etc.) para realizar el análisis interactivo.")

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

            # Verificar si está cargado Offers.csv
            offers_file = [name for name in dfs.keys() if "offers" in name.lower()]
            has_offers = len(offers_file) > 0

            # Normalizar nombre de la columna bucket_name tras los cruces
            bucket_col = [c for c in merged_data.columns if 'bucket_name' in c][0]

            # --- SECCIÓN 1: COMPARATIVA GLOBAL DE TODOS LOS 11 SEGMENTOS ---
            st.markdown("---")
            st.subheader("1. Visión General de Todos los Segmentos RFM (11 Segmentos)")
            
            segment_table_all = merged_data.groupby(bucket_col).agg(
                usuarios=('student_id', 'count'),
                gasto_total_eur=('gasto_total', 'sum'),
                ticket_medio_eur=('ticket_medio', 'mean'),
                frecuencia_media=('frecuencia', 'mean')
            ).reset_index()

            segment_table_all.rename(columns={bucket_col: 'Segmento'}, inplace=True)
            segment_table_all['ticket_medio_eur'] = segment_table_all['ticket_medio_eur'].round(2)
            segment_table_all['frecuencia_media'] = segment_table_all['frecuencia_media'].round(1)
            segment_table_all['gasto_total_eur'] = segment_table_all['gasto_total_eur'].round(2)

            st.dataframe(segment_table_all.sort_values(by='gasto_total_eur', ascending=False), use_container_width=True)

            # --- SECCIÓN DE FILTRADO DINÁMICO ---
            st.markdown("---")
            st.subheader("🎯 Seleccionar Segmento(s) a Analizar en Detalle")
            
            all_available_segments = sorted(merged_data[bucket_col].dropna().unique().tolist())
            
            selected_buckets = st.multiselect(
                "Elige los segmentos que quieres desplegar en las secciones inferiores (puedes añadir o borrar libremente):",
                options=all_available_segments,
                default=['1. Champions', '2. Loyal Active', '6. At Risk']
            )

            if not selected_buckets:
                st.warning("👆 Por favor selecciona al menos un segmento arriba para profundizar en los detalles inferiores.")
            else:
                filtered_merged = merged_data[merged_data[bucket_col].isin(selected_buckets)]

                # --- SECCIÓN 2: DEFENSA DE LOS SEGMENTOS SELECCIONADOS ---
                st.markdown("---")
                st.subheader("2. Ficha Comparativa de los Segmentos Seleccionados")

                cols = st.columns(len(selected_buckets))

                for idx, (col, seg) in enumerate(zip(cols, selected_buckets)):
                    df_seg = filtered_merged[filtered_merged[bucket_col] == seg]
                    with col:
                        st.markdown(f"### `{seg}`")
                        st.metric("Usuarios Únicos", f"{len(df_seg):,}")
                        st.metric("Ticket Medio", f"{df_seg['ticket_medio'].mean():.2f} €")
                        st.metric("Frecuencia Anual", f"{df_seg['frecuencia'].mean():.1f} visitas")
                        st.metric("Gasto Total", f"{df_seg['gasto_total'].sum():,.2f} €")

                        if 'points_balance' in df_seg.columns:
                            st.write(f"🏅 **Puntos (media):** {df_seg['points_balance'].mean():,.0f} pts")
                        if 'push_optin' in df_seg.columns:
                            st.write(f"📲 **Notificaciones Push:** {df_seg['push_optin'].mean()*100:.1f}%")

                # --- SECCIÓN 3: PERFIL DEMOGRÁFICO Y CANJES ---
                st.markdown("---")
                st.subheader("3. Perfil Demográfico (`persona`) y Hábitos de Canje (`redeemer_...`)")

                if not has_details:
                    st.info("ℹ️ Sube el archivo `Customers_details.csv` en la barra lateral para desbloquear el desglose por tipo de Persona.")
                else:
                    col_demo1, col_demo2 = st.columns(2)

                    with col_demo1:
                        st.markdown("#### 👤 Perfil Predominante (`persona`)")
                        persona_summary = filtered_merged.groupby([bucket_col, 'persona'])['student_id'].count().unstack().fillna(0)
                        persona_pct = persona_summary.div(persona_summary.sum(axis=1), axis=0) * 100
                        st.dataframe(persona_pct.round(1).astype(str) + " %", use_container_width=True)

                    with col_demo2:
                        st.markdown("#### 🍟 Hábitos de Canje de Productos (`redeemer_...`)")
                        redeemer_cols_all = [c for c in filtered_merged.columns if 'redeemer_' in c]
                        if redeemer_cols_all:
                            redemption_pct = (filtered_merged.groupby(bucket_col)[redeemer_cols_all].mean() * 100).round(1)
                            redemption_pct.columns = [c.replace('redeemer_', '').capitalize() for c in redemption_pct.columns]
                            st.dataframe(redemption_pct, use_container_width=True)

                # --- SECCIÓN 4: ANÁLISIS DETALLADO DE COMPRAS Y OFERTAS (ventas.csv + Offers.csv) ---
                st.markdown("---")
                st.subheader("4. ¿Qué Compran Exactamente? — Análisis de Ofertas (`Offers.csv`) y Horarios (`daypart`)")

                # A. Momento del día (daypart)
                if 'daypart' in df_ventas.columns:
                    st.markdown("#### ⏰ Distribución por Franja Horaria de Compra (`daypart`)")
                    ventas_targets = df_ventas[df_ventas['bucket_name'].isin(selected_buckets)]
                    daypart_summary = ventas_targets.groupby(['bucket_name', 'daypart'])['sale_id'].nunique().unstack().fillna(0)
                    daypart_pct = daypart_summary.div(daypart_summary.sum(axis=1), axis=0) * 100
                    st.dataframe(daypart_pct.round(1).astype(str) + " %", use_container_width=True)

                # B. Cruce exacto con Offers.csv (Limpiando prefijo 500)
                if not has_offers:
                    st.info("ℹ️ Carga el archivo `Offers.csv` para ver las ofertas y promociones específicas que compran estos usuarios.")
                else:
                    st.markdown("#### 🏷️ Top Ofertas y Menús Comprados (`Offers.csv`)")
                    df_offers = dfs[offers_file[0]]

                    # Filtrar ventas de los segmentos seleccionados con ofertas
                    ventas_with_offers = df_ventas[df_ventas['bucket_name'].isin(selected_buckets)].dropna(subset=['offerids']).copy()

                    if ventas_with_offers.empty:
                        st.info("No hay registros de compras con ofertas para los segmentos seleccionados.")
                    else:
                        # Explotar offerids separados por comas
                        ventas_with_offers['offer_id_raw'] = ventas_with_offers['offerids'].astype(str).str.split(',')
                        exploded_ventas = ventas_with_offers.explode('offer_id_raw')
                        exploded_ventas['offer_id_clean'] = exploded_ventas['offer_id_raw'].str.strip()

                        # PRECAUCIÓN: Eliminar el prefijo '500' de cada offer_id
                        exploded_ventas['offer_id'] = exploded_ventas['offer_id_clean'].apply(
                            lambda x: int(x[3:]) if str(x).startswith('500') and len(str(x)) > 3 and str(x)[3:].isdigit() else None
                        )

                        # Cruce con Offers.csv
                        merged_offers = pd.merge(exploded_ventas, df_offers, on='offer_id', how='inner')

                        col_off1, col_demo2 = st.columns(2)

                        with col_off1:
                            st.markdown("**Top 10 Títulos de Ofertas/Menús Más Comprados:**")
                            top_titles = merged_offers.groupby(['bucket_name', 'title'])['sale_id'].count().reset_index()
                            top_titles.columns = ['Segmento', 'Título Oferta / Producto', 'Veces Comprado']
                            top_titles = top_titles.sort_values(by='Veces Comprado', ascending=False).groupby('Segmento').head(5)
                            st.dataframe(top_titles, use_container_width=True)

                        with col_demo2:
                            st.markdown("**Estrategia de Marketing Usada (`marketing_sublayer`):**")
                            if 'marketing_sublayer' in merged_offers.columns:
                                sublayer_summary = merged_offers.groupby(['bucket_name', 'marketing_sublayer'])['sale_id'].count().unstack().fillna(0)
                                sublayer_pct = sublayer_summary.div(sublayer_summary.sum(axis=1), axis=0) * 100
                                st.dataframe(sublayer_pct.round(1).astype(str) + " %", use_container_width=True)

                # --- SECCIÓN 5: ENGAGEMENT POR FIDELIZACIÓN ---
                st.markdown("---")
                st.subheader("5. Nivel de Engagement por Fidelización (Segmentos Seleccionados)")

                if not has_details:
                    st.info("ℹ️ Carga `Customers_details.csv` para ver las métricas de lealtad.")
                else:
                    redeemer_cols_all = [c for c in filtered_merged.columns if 'redeemer_' in c]
                    filtered_merged['total_canjes_familias'] = filtered_merged[redeemer_cols_all].sum(axis=1)

                    loyalty_engagement = filtered_merged.groupby(bucket_col).agg(
                        pct_usuarios_que_canjean=('points_burned', lambda x: (x < 0).mean() * 100),
                        puntos_ganados_media=('points_earned', 'mean'),
                        puntos_canjeados_media=('points_burned', 'mean'),
                        saldo_puntos_media=('points_balance', 'mean'),
                        familias_productos_canjeadas=('total_canjes_familias', 'mean')
                    ).reset_index()

                    loyalty_engagement.rename(columns={bucket_col: 'Segmento'}, inplace=True)
                    
                    loyalty_display = loyalty_engagement.copy()
                    loyalty_display['pct_usuarios_que_canjean'] = loyalty_display['pct_usuarios_que_canjean'].round(1).astype(str) + " %"
                    loyalty_display['puntos_ganados_media'] = loyalty_display['puntos_ganados_media'].round(0)
                    loyalty_display['puntos_canjeados_media'] = loyalty_display['puntos_canjeados_media'].round(0)
                    loyalty_display['saldo_puntos_media'] = loyalty_display['saldo_puntos_media'].round(0)
                    loyalty_display['familias_productos_canjeadas'] = loyalty_display['familias_productos_canjeadas'].round(2)

                    st.dataframe(loyalty_display, use_container_width=True)

                # --- SECCIÓN 6: ESTRATEGIA Y RECOMENDACIÓN DE NEGOCIO ---
                st.markdown("---")
                st.subheader("6. Argumentario de Negocio para la Presentación (3 Diapositivas)")
                
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
