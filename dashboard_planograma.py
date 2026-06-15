"""
Dashboard Planograma OXXO — Streamlit
Paleta: Rojo OXXO (#E3000F), Blanco, Amarillo (#FFD100), Gris oscuro (#1A1A1A)

Ejecutar:
    streamlit run dashboard_planograma.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Planograma OXXO",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta de colores ────────────────────────────────────────────────────────
ROJO    = "#E3000F"
AMARILLO= "#FFD100"
BLANCO  = "#FFFFFF"
GRIS    = "#1A1A1A"
ROJO_SUAVE = "#FF4B55"
ROJO_CLARO = "#FFE5E7"

# ── CSS personalizado ────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    /* Fondo general */
    .stApp {{ background-color: #F5F5F5; }}

    /* Header superior */
    header[data-testid="stHeader"] {{
        background-color: {ROJO};
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {GRIS};
        color: {BLANCO};
    }}
    [data-testid="stSidebar"] * {{
        color: {BLANCO} !important;
    }}
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stSlider label {{
        color: {AMARILLO} !important;
        font-weight: 600;
    }}

    /* KPI Cards */
    .kpi-card {{
        background: {BLANCO};
        border-left: 6px solid {ROJO};
        border-radius: 10px;
        padding: 18px 22px;
        margin: 6px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    .kpi-card .kpi-value {{
        font-size: 2rem;
        font-weight: 800;
        color: {ROJO};
        line-height: 1;
    }}
    .kpi-card .kpi-label {{
        font-size: 0.82rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 4px;
    }}
    .kpi-card .kpi-delta {{
        font-size: 0.85rem;
        color: {AMARILLO};
        font-weight: 700;
    }}

    /* Título principal */
    .main-title {{
        background: linear-gradient(90deg, {ROJO} 0%, #8B0008 100%);
        color: {BLANCO};
        padding: 18px 28px;
        border-radius: 12px;
        margin-bottom: 20px;
    }}
    .main-title h1 {{ color: {BLANCO}; margin: 0; font-size: 1.8rem; }}
    .main-title p  {{ color: rgba(255,255,255,0.85); margin: 4px 0 0; font-size: 0.9rem; }}

    /* Tab activo */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {BLANCO};
        border-radius: 8px;
        padding: 4px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {ROJO} !important;
        color: {BLANCO} !important;
        border-radius: 6px;
    }}

    /* Tabla */
    .stDataFrame {{ border-radius: 8px; overflow: hidden; }}

    /* Sección titles */
    .section-title {{
        color: {ROJO};
        font-size: 1.1rem;
        font-weight: 700;
        border-bottom: 3px solid {AMARILLO};
        padding-bottom: 4px;
        margin: 20px 0 14px;
    }}

    /* Badge */
    .badge {{
        display: inline-block;
        background: {ROJO};
        color: {BLANCO};
        border-radius: 12px;
        padding: 3px 10px;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 2px;
    }}

    /* Alerta info */
    .info-box {{
        background: {ROJO_CLARO};
        border: 1px solid {ROJO};
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 0.88rem;
        color: {GRIS};
    }}
</style>
""", unsafe_allow_html=True)

# ── Carga de datos ───────────────────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "output_planograma_todos.csv"

@st.cache_data(show_spinner="Cargando datos del planograma…")
def cargar_datos(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df["TAMANO_DESC"] = pd.to_numeric(df["TAMANO_DESC"], errors="coerce")
    return df

if not DATA_FILE.exists():
    st.error(f"No se encontró `{DATA_FILE.name}`. Ejecuta primero el notebook para generar el consolidado.")
    st.stop()

df_raw = cargar_datos(DATA_FILE)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-title">
  <h1>🏪 Dashboard Planograma OXXO — Mueble CF</h1>
  <p>Análisis interactivo · Algoritmo Best-Fit + 2-opt · {len(df_raw):,} registros · {df_raw["SEGMENTO_ID"].nunique()} segmentos</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📊  Resultados Generales",
    "🔍  Explorador de Datos",
    "🎛️  Simulador de Escenarios",
])

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TAB 1 — RESULTADOS GENERALES                                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝
with tab1:

    # ── KPI Cards ──
    st.markdown('<div class="section-title">Métricas Clave del Planograma</div>', unsafe_allow_html=True)

    total_skus       = df_raw["UPC_CVE"].nunique()
    total_registros  = len(df_raw)
    total_frentes    = df_raw["NUM_FRENTES"].sum()
    charolas_max     = df_raw["CHAROLA_ID"].max()
    tiempo_total     = df_raw["TIEMPO_COMPUTO_S"].max()  # máximo por planograma
    ancho_prom       = df_raw["ANCHO_DIBUJO_CM"].mean()
    frentes_prom     = df_raw["NUM_FRENTES"].mean()
    n_segmentos      = df_raw["SEGMENTO_ID"].nunique()
    n_direcciones    = df_raw["DIRECCION"].nunique()

    # Calcular ocupación promedio por charola/planograma
    WIDTH_MAX = 120.0
    df_charola = (
        df_raw.groupby(["SEGMENTO_ID", "DIRECCION", "TAMANO_DESC", "CHAROLA_ID"])
        ["ANCHO_DIBUJO_CM"].sum().reset_index()
    )
    df_charola["ocup_pct"] = (df_charola["ANCHO_DIBUJO_CM"] / WIDTH_MAX * 100).clip(0, 100)
    ocup_prom = df_charola["ocup_pct"].mean()

    c1, c2, c3, c4, c5 = st.columns(5)
    kpis = [
        (c1, f"{total_skus:,}",      "SKUs únicos",           f"{n_segmentos} segmentos"),
        (c2, f"{total_frentes:,}",   "Total de frentes",      f"~{frentes_prom:.1f} frentes/SKU"),
        (c3, f"{ocup_prom:.1f}%",    "Ocupación promedio",    "del ancho de charola"),
        (c4, f"{int(charolas_max)}",  "Charolas máx. usadas",  "en un planograma"),
        (c5, f"{ancho_prom:.1f} cm", "Ancho dibujo promedio", "por producto"),
    ]
    for col, val, label, delta in kpis:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-value">{val}</div>
              <div class="kpi-label">{label}</div>
              <div class="kpi-delta">{delta}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")

    # ── Gráficos generales ──
    col_g1, col_g2 = st.columns([3, 2])

    with col_g1:
        st.markdown('<div class="section-title">Frentes totales por Segmento</div>', unsafe_allow_html=True)
        seg_frentes = (
            df_raw.groupby("SEGMENTO_ID")["NUM_FRENTES"]
            .sum().reset_index().sort_values("NUM_FRENTES", ascending=True)
        )
        fig_bar = px.bar(
            seg_frentes, x="NUM_FRENTES", y="SEGMENTO_ID",
            orientation="h", text="NUM_FRENTES",
            color="NUM_FRENTES",
            color_continuous_scale=[[0, ROJO_CLARO], [0.4, ROJO_SUAVE], [1, ROJO]],
        )
        fig_bar.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_bar.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            coloraxis_showscale=False,
            xaxis_title="Total frentes", yaxis_title="",
            margin=dict(l=0, r=30, t=10, b=0), height=320,
            font=dict(family="sans-serif"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_g2:
        st.markdown('<div class="section-title">SKUs por Planogrupo (Top 8)</div>', unsafe_allow_html=True)
        top_pg = (
            df_raw.groupby("PLANOGRUPO_DESC")["UPC_CVE"]
            .nunique().reset_index().rename(columns={"UPC_CVE": "skus"})
            .sort_values("skus", ascending=False).head(8)
        )
        fig_pie = px.pie(
            top_pg, values="skus", names="PLANOGRUPO_DESC",
            color_discrete_sequence=[ROJO, AMARILLO, "#FF6B6B", "#FFE066",
                                     "#CC0009", "#FFC300", "#FF4B55", "#FFD700"],
            hole=0.42,
        )
        fig_pie.update_traces(textposition="outside", textinfo="percent+label")
        fig_pie.update_layout(
            paper_bgcolor="white", showlegend=False,
            margin=dict(l=0, r=0, t=10, b=0), height=320,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Ocupación por segmento ──
    st.markdown('<div class="section-title">Ocupación promedio de charola por Segmento y Dirección</div>', unsafe_allow_html=True)
    ocup_seg = (
        df_charola.merge(
            df_raw[["SEGMENTO_ID", "DIRECCION", "TAMANO_DESC", "CHAROLA_ID"]].drop_duplicates(),
            on=["SEGMENTO_ID", "DIRECCION", "TAMANO_DESC", "CHAROLA_ID"],
        )
        .groupby(["SEGMENTO_ID", "DIRECCION"])["ocup_pct"]
        .mean().reset_index()
    )
    fig_ocup = px.bar(
        ocup_seg, x="SEGMENTO_ID", y="ocup_pct", color="DIRECCION",
        barmode="group", text_auto=".1f",
        color_discrete_map={"DI": ROJO, "IZ": AMARILLO},
        labels={"ocup_pct": "Ocupación (%)", "SEGMENTO_ID": "Segmento"},
    )
    fig_ocup.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        yaxis_range=[0, 105], margin=dict(l=0, r=0, t=10, b=0), height=300,
        legend_title="Dirección",
    )
    fig_ocup.add_hline(y=80, line_dash="dash", line_color="green",
                       annotation_text="Meta 80%", annotation_position="top right")
    st.plotly_chart(fig_ocup, use_container_width=True)

    # ── Distribución de SKUs por charola ──
    st.markdown('<div class="section-title">Distribución: SKUs por charola</div>', unsafe_allow_html=True)
    skus_x_charola = (
        df_raw.groupby(["SEGMENTO_ID", "DIRECCION", "TAMANO_DESC", "CHAROLA_ID"])
        ["UPC_CVE"].nunique().reset_index(name="n_skus")
    )
    fig_hist = px.histogram(
        skus_x_charola, x="n_skus", nbins=10,
        color_discrete_sequence=[ROJO],
        labels={"n_skus": "SKUs por charola", "count": "Frecuencia"},
    )
    fig_hist.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=0, r=0, t=10, b=0), height=250,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TAB 2 — EXPLORADOR DE DATOS                                            ║
# ╚══════════════════════════════════════════════════════════════════════════╝
with tab2:

    # ── Sidebar filtros ──
    with st.sidebar:
        st.markdown(f"<h2 style='color:{AMARILLO};margin-top:0'>🔧 Filtros</h2>", unsafe_allow_html=True)

        seg_opts = sorted(df_raw["SEGMENTO_ID"].dropna().unique())
        seg_sel  = st.multiselect("Segmento", seg_opts, default=seg_opts[:2],
                                  help="Selecciona uno o varios segmentos")

        dir_opts = sorted(df_raw["DIRECCION"].dropna().unique())
        dir_sel  = st.multiselect("Dirección", dir_opts, default=dir_opts,
                                  help="DI = Derecha, IZ = Izquierda")

        tam_min, tam_max = float(df_raw["TAMANO_DESC"].min()), float(df_raw["TAMANO_DESC"].max())
        tam_rango = st.slider("Tamaño de puerta", tam_min, tam_max,
                              (tam_min, tam_max), step=0.5,
                              help="Rango de TAMANO_DESC")

        pg_opts  = sorted(df_raw["PLANOGRUPO_DESC"].dropna().unique())
        pg_sel   = st.multiselect("Planogrupo", pg_opts, default=[],
                                  help="Deja vacío para ver todos")

        st.markdown("---")
        st.markdown(f"<small style='color:#aaa'>Datos: output_planograma_todos.csv<br>{len(df_raw):,} registros totales</small>",
                    unsafe_allow_html=True)

    # ── Aplicar filtros ──
    mask = (
        df_raw["SEGMENTO_ID"].isin(seg_sel if seg_sel else seg_opts) &
        df_raw["DIRECCION"].isin(dir_sel if dir_sel else dir_opts) &
        df_raw["TAMANO_DESC"].between(tam_rango[0], tam_rango[1])
    )
    if pg_sel:
        mask &= df_raw["PLANOGRUPO_DESC"].isin(pg_sel)

    df_fil = df_raw[mask].copy()

    n_fil = len(df_fil)
    st.markdown(
        f'<div class="info-box">🔎 Mostrando <b>{n_fil:,}</b> registros con los filtros actuales '
        f'({n_fil/len(df_raw)*100:.1f}% del total)</div>',
        unsafe_allow_html=True,
    )

    if df_fil.empty:
        st.warning("Sin datos con los filtros seleccionados.")
    else:
        col_v1, col_v2 = st.columns([2, 1])

        with col_v1:
            st.markdown('<div class="section-title">Frentes por Segmento (filtrado)</div>', unsafe_allow_html=True)
            seg_f = (
                df_fil.groupby(["SEGMENTO_ID", "DIRECCION"])["NUM_FRENTES"]
                .sum().reset_index()
            )
            fig_f = px.bar(
                seg_f, x="SEGMENTO_ID", y="NUM_FRENTES", color="DIRECCION",
                barmode="group", text_auto=",",
                color_discrete_map={"DI": ROJO, "IZ": AMARILLO},
                labels={"NUM_FRENTES": "Total frentes", "SEGMENTO_ID": "Segmento"},
            )
            fig_f.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=0, r=0, t=10, b=0), height=300,
            )
            st.plotly_chart(fig_f, use_container_width=True)

        with col_v2:
            st.markdown('<div class="section-title">Top 10 productos</div>', unsafe_allow_html=True)
            top10 = (
                df_fil.groupby("ITEM_DESC")["NUM_FRENTES"]
                .sum().reset_index().sort_values("NUM_FRENTES", ascending=True).tail(10)
            )
            fig_top = px.bar(
                top10, x="NUM_FRENTES", y="ITEM_DESC",
                orientation="h", text="NUM_FRENTES",
                color_discrete_sequence=[ROJO],
                labels={"NUM_FRENTES": "Frentes", "ITEM_DESC": ""},
            )
            fig_top.update_traces(texttemplate="%{text}", textposition="outside")
            fig_top.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=0, r=30, t=10, b=0), height=300,
                yaxis=dict(tickfont=dict(size=10)),
            )
            st.plotly_chart(fig_top, use_container_width=True)

        # ── Visualizador de charola ──
        st.markdown('<div class="section-title">Visualizador de Charola (planograma)</div>', unsafe_allow_html=True)

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            seg_v  = st.selectbox("Segmento", sorted(df_fil["SEGMENTO_ID"].unique()), key="vis_seg")
        with col_p2:
            dir_v  = st.selectbox("Dirección", sorted(df_fil[df_fil["SEGMENTO_ID"]==seg_v]["DIRECCION"].unique()), key="vis_dir")
        with col_p3:
            tams   = sorted(df_fil[(df_fil["SEGMENTO_ID"]==seg_v) & (df_fil["DIRECCION"]==dir_v)]["TAMANO_DESC"].unique())
            tam_v  = st.selectbox("Tamaño", tams, key="vis_tam")

        df_vis = df_fil[
            (df_fil["SEGMENTO_ID"]==seg_v) &
            (df_fil["DIRECCION"]==dir_v) &
            (df_fil["TAMANO_DESC"]==tam_v)
        ].copy()

        if not df_vis.empty:
            charolas_ids = sorted(df_vis["CHAROLA_ID"].unique())

            # paleta de colores para planogrupos
            pgs = df_vis["PLANOGRUPO_DESC"].unique()
            colors_pg = {}
            palette = [ROJO, AMARILLO, "#FF6B6B", "#FFD700", "#CC0009",
                       "#FFC300", "#FF4B55", "#B8860B", "#DC143C", "#DAA520"]
            for i, pg in enumerate(pgs):
                colors_pg[pg] = palette[i % len(palette)]

            fig_shelf = go.Figure()
            n_charolas = len(charolas_ids)
            height_cm  = 20   # altura visual por charola

            for row_i, ch_id in enumerate(charolas_ids):
                df_ch = df_vis[df_vis["CHAROLA_ID"] == ch_id]
                y_base = (n_charolas - row_i - 1) * (height_cm + 5)

                # Fondo de la charola
                fig_shelf.add_shape(
                    type="rect",
                    x0=0, x1=120, y0=y_base, y1=y_base + height_cm,
                    fillcolor="#F0F0F0", line=dict(color="#CCC", width=1),
                )

                for _, prod in df_ch.iterrows():
                    x0 = prod["COORDENADA_X_INICIO"]
                    x1 = x0 + prod["ANCHO_DIBUJO_CM"]
                    color_fill = colors_pg.get(prod["PLANOGRUPO_DESC"], ROJO)
                    fig_shelf.add_shape(
                        type="rect",
                        x0=x0, x1=x1, y0=y_base + 1, y1=y_base + height_cm - 1,
                        fillcolor=color_fill, opacity=0.85,
                        line=dict(color=BLANCO, width=1),
                    )
                    # Etiqueta del producto si hay espacio
                    if prod["ANCHO_DIBUJO_CM"] >= 8:
                        desc = str(prod["ITEM_DESC"])[:18]
                        fig_shelf.add_annotation(
                            x=(x0 + x1) / 2, y=y_base + height_cm / 2,
                            text=desc, showarrow=False,
                            font=dict(size=7, color=BLANCO if color_fill != AMARILLO else GRIS),
                            xanchor="center", yanchor="middle",
                            textangle=-90 if prod["ANCHO_DIBUJO_CM"] < 14 else 0,
                        )

                # Etiqueta de charola
                fig_shelf.add_annotation(
                    x=-3, y=y_base + height_cm / 2,
                    text=f"Ch.{ch_id}", showarrow=False,
                    font=dict(size=10, color=GRIS), xanchor="right",
                )

            fig_shelf.update_layout(
                height=max(300, n_charolas * 55),
                paper_bgcolor=BLANCO, plot_bgcolor=BLANCO,
                margin=dict(l=50, r=20, t=20, b=20),
                xaxis=dict(range=[-5, 125], title="Ancho (cm)",
                           showgrid=True, gridcolor="#EEE"),
                yaxis=dict(visible=False),
                title=dict(text=f"Planograma: {seg_v} / {dir_v} / Tamaño {tam_v}",
                           font=dict(color=ROJO, size=14)),
            )

            # Leyenda de planogrupos
            for pg, col_ in colors_pg.items():
                fig_shelf.add_trace(go.Scatter(
                    x=[None], y=[None], mode="markers",
                    marker=dict(size=12, color=col_, symbol="square"),
                    name=pg, showlegend=True,
                ))

            st.plotly_chart(fig_shelf, use_container_width=True)

        # ── Tabla de datos ──
        st.markdown('<div class="section-title">Tabla de datos filtrada</div>', unsafe_allow_html=True)
        cols_show = ["SEGMENTO_ID", "DIRECCION", "TAMANO_DESC", "CHAROLA_ID",
                     "ITEM_DESC", "PLANOGRUPO_DESC", "NUM_FRENTES",
                     "COORDENADA_X_INICIO", "ANCHO_DIBUJO_CM"]
        st.dataframe(
            df_fil[cols_show].reset_index(drop=True),
            use_container_width=True, height=320,
        )

        csv_bytes = df_fil[cols_show].to_csv(index=False).encode()
        st.download_button(
            "⬇️ Descargar filtrado como CSV", csv_bytes,
            file_name="planograma_filtrado.csv", mime="text/csv",
        )

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TAB 3 — SIMULADOR                                                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝
with tab3:
    st.markdown('<div class="section-title">Parámetros del Simulador</div>', unsafe_allow_html=True)
    st.markdown("""
    Modifica los parámetros del algoritmo de bin-packing y observa cómo cambian
    la ocupación estimada y el número de charolas necesarias por segmento.
    """)

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        sim_width    = st.slider("Ancho máximo de charola (cm)", 80, 200, 120, 5,
                                 help="WIDTH_MAX del algoritmo")
        sim_sep      = st.slider("Separación entre productos (cm)", 0.0, 3.0, 0.5, 0.1)
    with col_s2:
        sim_max_skus = st.slider("Máx. SKUs por charola", 3, 20, 10,
                                 help="MAX_SKUS_POR_CHAROLA")
        sim_eye_bon  = st.slider("Bono charolas ojo (×)", 1.0, 3.0, 1.5, 0.1,
                                 help="Factor multiplicador para charolas eye-level")
    with col_s3:
        sim_seg_list = st.multiselect(
            "Segmentos a simular", sorted(df_raw["SEGMENTO_ID"].unique()),
            default=sorted(df_raw["SEGMENTO_ID"].unique()),
        )
        sim_dir      = st.selectbox("Dirección a simular", ["DI", "IZ", "Ambas"])

    st.markdown("")

    # ── Lógica de simulación ─────────────────────────────────────────────────
    # Parámetros actuales (baseline del notebook)
    BASE_WIDTH    = 120.0
    BASE_SEP      = 0.5
    BASE_MAX_SKUS = 10
    EYE_BON       = 1.5

    dir_filtro = df_raw["DIRECCION"].unique() if sim_dir == "Ambas" else [sim_dir]

    resultados = []
    for seg in (sim_seg_list or sorted(df_raw["SEGMENTO_ID"].unique())):
        df_s = df_raw[
            (df_raw["SEGMENTO_ID"] == seg) &
            (df_raw["DIRECCION"].isin(dir_filtro))
        ]
        if df_s.empty:
            continue

        # ── Estimación baseline ──
        # Número de charolas ≈ ceil(ancho_total / (WIDTH_MAX * factor_skus))
        ancho_total    = df_s["ANCHO_DIBUJO_CM"].sum()
        n_skus_uniq    = df_s["UPC_CVE"].nunique()
        frentes_tot    = df_s["NUM_FRENTES"].sum()

        # Charolas reales en los datos
        charolas_reales = df_s.groupby(["DIRECCION", "TAMANO_DESC", "CHAROLA_ID"]).ngroups

        # Estimación charolas base
        espacio_efectivo_base = BASE_WIDTH - (n_skus_uniq / BASE_MAX_SKUS) * BASE_SEP
        charolas_base = max(1, int(np.ceil(ancho_total / max(espacio_efectivo_base, 1))))
        ocup_base     = min(100, ancho_total / (charolas_base * BASE_WIDTH) * 100)

        # ── Estimación simulada ──
        espacio_efectivo_sim = sim_width - (n_skus_uniq / sim_max_skus) * sim_sep
        charolas_sim = max(1, int(np.ceil(ancho_total / max(espacio_efectivo_sim, 1))))
        ocup_sim     = min(100, ancho_total / (charolas_sim * sim_width) * 100)

        # Score objetivo (con bono eye-level ≈ primeras 2 charolas)
        eye_charolas      = min(2, charolas_base)
        eye_charolas_sim  = min(2, charolas_sim)
        score_base = (frentes_tot * (1 + (eye_charolas / max(charolas_base, 1)) * (EYE_BON - 1)))
        score_sim  = (frentes_tot * (1 + (eye_charolas_sim / max(charolas_sim, 1)) * (sim_eye_bon - 1)))

        resultados.append({
            "Segmento":          seg,
            "Charolas (actual)": charolas_base,
            "Charolas (sim.)":   charolas_sim,
            "Δ Charolas":        charolas_sim - charolas_base,
            "Ocup. actual (%)":  round(ocup_base, 1),
            "Ocup. sim. (%)":    round(ocup_sim, 1),
            "Δ Ocup. (pp)":      round(ocup_sim - ocup_base, 1),
            "Score actual":      round(score_base, 0),
            "Score sim.":        round(score_sim, 0),
            "Δ Score":           round(score_sim - score_base, 0),
        })

    if not resultados:
        st.info("Selecciona al menos un segmento para simular.")
    else:
        df_sim = pd.DataFrame(resultados)

        # ── Tabla comparativa ──
        st.markdown('<div class="section-title">Tabla Comparativa: Actual vs Simulado</div>', unsafe_allow_html=True)

        def color_delta(val):
            if isinstance(val, (int, float)):
                if val > 0:
                    return "color: #28a745; font-weight:700"
                elif val < 0:
                    return "color: #E3000F; font-weight:700"
            return ""

        styled = (
            df_sim.style
            .map(color_delta, subset=["Δ Charolas", "Δ Ocup. (pp)", "Δ Score"])
            .format({
                "Ocup. actual (%)": "{:.1f}%",
                "Ocup. sim. (%)":   "{:.1f}%",
                "Δ Ocup. (pp)":     "{:+.1f}",
                "Δ Score":          "{:+.0f}",
            })
        )
        st.dataframe(styled, use_container_width=True, height=350)

        # ── Gráficos comparativos ──
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown('<div class="section-title">Ocupación: Actual vs Simulado</div>', unsafe_allow_html=True)
            df_melt = df_sim[["Segmento", "Ocup. actual (%)", "Ocup. sim. (%)"]].melt(
                id_vars="Segmento", var_name="Escenario", value_name="Ocupación (%)"
            )
            fig_ocup_sim = px.bar(
                df_melt, x="Segmento", y="Ocupación (%)",
                color="Escenario", barmode="group", text_auto=".1f",
                color_discrete_map={"Ocup. actual (%)": ROJO, "Ocup. sim. (%)": AMARILLO},
            )
            fig_ocup_sim.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                yaxis_range=[0, 110], height=320,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            fig_ocup_sim.add_hline(y=80, line_dash="dash", line_color="green",
                                   annotation_text="Meta 80%")
            st.plotly_chart(fig_ocup_sim, use_container_width=True)

        with col_g2:
            st.markdown('<div class="section-title">Charolas necesarias: Actual vs Simulado</div>', unsafe_allow_html=True)
            df_melt2 = df_sim[["Segmento", "Charolas (actual)", "Charolas (sim.)"]].melt(
                id_vars="Segmento", var_name="Escenario", value_name="Charolas"
            )
            fig_ch_sim = px.bar(
                df_melt2, x="Segmento", y="Charolas",
                color="Escenario", barmode="group", text_auto=",",
                color_discrete_map={"Charolas (actual)": ROJO, "Charolas (sim.)": AMARILLO},
            )
            fig_ch_sim.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                height=320, margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig_ch_sim, use_container_width=True)

        # ── Score objetivo ──
        st.markdown('<div class="section-title">Score objetivo (frentes × bono eye-level)</div>', unsafe_allow_html=True)
        df_melt3 = df_sim[["Segmento", "Score actual", "Score sim."]].melt(
            id_vars="Segmento", var_name="Escenario", value_name="Score"
        )
        fig_score = px.line(
            df_melt3, x="Segmento", y="Score", color="Escenario",
            markers=True, text="Score",
            color_discrete_map={"Score actual": ROJO, "Score sim.": AMARILLO},
            labels={"Score": "Score objetivo"},
        )
        fig_score.update_traces(textposition="top center", texttemplate="%{text:,.0f}")
        fig_score.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            height=280, margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_score, use_container_width=True)

        # ── Resumen ejecutivo ──
        total_d_charolas = df_sim["Δ Charolas"].sum()
        total_d_ocup     = df_sim["Δ Ocup. (pp)"].mean()
        total_d_score    = df_sim["Δ Score"].sum()

        st.markdown('<div class="section-title">Resumen del impacto simulado</div>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        signo = lambda x: f"+{x:,.0f}" if x >= 0 else f"{x:,.0f}"

        with m1:
            color_card = ROJO if total_d_charolas > 0 else "#1A7A3F"
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color:{color_card}">
              <div class="kpi-value" style="color:{color_card}">{signo(total_d_charolas)}</div>
              <div class="kpi-label">Δ Charolas totales</div>
              <div class="kpi-delta">vs. configuración actual</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            color_card = "#1A7A3F" if total_d_ocup >= 0 else ROJO
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color:{color_card}">
              <div class="kpi-value" style="color:{color_card}">{signo(total_d_ocup)} pp</div>
              <div class="kpi-label">Δ Ocupación promedio</div>
              <div class="kpi-delta">puntos porcentuales</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            color_card = "#1A7A3F" if total_d_score >= 0 else ROJO
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color:{color_card}">
              <div class="kpi-value" style="color:{color_card}">{signo(total_d_score)}</div>
              <div class="kpi-label">Δ Score objetivo total</div>
              <div class="kpi-delta">suma de todos los segmentos</div>
            </div>
            """, unsafe_allow_html=True)
