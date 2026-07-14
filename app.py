import re
import unicodedata
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="Matrícula Diplomados y Postítulos — Chile",
    page_icon="🎓",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
NARANJA = "#F2653C"
GRIS_CLARO = "#EDEAE3"
NEGRO = "#232323"

st.markdown(
    f"""
    <style>
    .kpi-card {{
        border-radius: 6px;
        padding: 22px 24px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 18px;
    }}
    .kpi-card.light {{ background-color: {GRIS_CLARO}; }}
    .kpi-card.dark {{ background-color: {NEGRO}; }}
    .kpi-number {{
        font-size: 2.6rem;
        font-weight: 800;
        color: {NARANJA};
        line-height: 1;
        white-space: nowrap;
    }}
    .kpi-text {{
        font-size: 0.95rem;
        line-height: 1.3;
    }}
    .kpi-card.light .kpi-text {{ color: #333; }}
    .kpi-card.dark .kpi-text {{ color: #FFFFFF; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("matricula_diplomados_postitulos.csv.gz")
    return df

df = load_data()

st.title("🎓 Matrícula de Diplomados y Postítulos en Chile")
st.caption(
    "Fuente: Matrícula SIES/mifuturo.cl 2007–2025. Filtrado por "
    "**NIVEL GLOBAL = 'Postítulo'** y **CARRERA CLASIFICACIÓN NIVEL 1** en "
    "**'Diplomado (desde un semestre)'** o **'Postítulo'**. Incluye todas las "
    "instituciones del sistema (Universidades, Institutos Profesionales y CFT)."
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Réplica del panel: gráfico + 3 KPIs
# ---------------------------------------------------------------------------
años_disponibles = sorted(df[df["Año"] >= 2020]["Año"].unique())
rango = st.select_slider(
    "Rango de años a comparar en las tarjetas de la derecha",
    options=años_disponibles,
    value=(años_disponibles[0], años_disponibles[-1]),
    key="rango_años",
)

# El gráfico siempre muestra desde 2020 en adelante, sin importar el rango elegido
mat_year = df[df["Año"] >= 2020].groupby("Año")["TOTAL MATRÍCULA"].sum().reset_index()

col_chart, col_kpi = st.columns([2, 1])

with col_chart:
    fig = go.Figure(
        go.Bar(
            x=mat_year["Año"].astype(str),
            y=mat_year["TOTAL MATRÍCULA"],
            marker_color=NARANJA,
            text=mat_year["TOTAL MATRÍCULA"].apply(lambda x: f"{x:,.0f}".replace(",", ".")),
            textposition="outside",
        )
    )
    fig.update_layout(
        showlegend=False,
        yaxis=dict(visible=False),
        xaxis=dict(title=None, tickfont=dict(size=16)),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=10, b=10, l=10, r=10),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "<p style='font-style:italic; color:#666; margin-top:-10px;'>"
        "Matrícula total sistema — diplomados y postítulos</p>",
        unsafe_allow_html=True,
    )

with col_kpi:
    # KPI 1: variación total entre los dos años extremos del rango
    y_ini, y_fin = rango
    v_ini = df[df["Año"] == y_ini]["TOTAL MATRÍCULA"].sum()
    v_fin = df[df["Año"] == y_fin]["TOTAL MATRÍCULA"].sum()
    var_total = (v_fin - v_ini) / v_ini * 100 if v_ini else 0

    st.markdown(
        f"""
        <div class="kpi-card light">
            <div class="kpi-number">{var_total:+.0f}%</div>
            <div class="kpi-text">creció la matrícula del sistema entre {y_ini} y {y_fin}
            ({v_ini:,.0f} → {v_fin:,.0f})</div>
        </div>
        """.replace(",", "."),
        unsafe_allow_html=True,
    )

    # KPI 2: variación en área "Salud"
    salud = df[df["ÁREA DEL CONOCIMIENTO"] == "Salud"]
    s_ini = salud[salud["Año"] == y_ini]["TOTAL MATRÍCULA"].sum()
    s_fin = salud[salud["Año"] == y_fin]["TOTAL MATRÍCULA"].sum()
    var_salud = (s_fin - s_ini) / s_ini * 100 if s_ini else 0

    st.markdown(
        f"""
        <div class="kpi-card dark">
            <div class="kpi-number">{var_salud:+.0f}%</div>
            <div class="kpi-text">creció el área Salud entre {y_ini} y {y_fin}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # KPI 3: % no presencial en el año final, vs año inicial
    d_fin = df[df["Año"] == y_fin]
    d_ini = df[df["Año"] == y_ini]
    pct_np_fin = d_fin[d_fin["MODALIDAD"] == "No Presencial"]["TOTAL MATRÍCULA"].sum() / d_fin["TOTAL MATRÍCULA"].sum() * 100
    pct_np_ini = d_ini[d_ini["MODALIDAD"] == "No Presencial"]["TOTAL MATRÍCULA"].sum() / d_ini["TOTAL MATRÍCULA"].sum() * 100
    n_np_fin = d_fin[d_fin["MODALIDAD"] == "No Presencial"]["TOTAL MATRÍCULA"].sum()

    st.markdown(
        f"""
        <div class="kpi-card light">
            <div class="kpi-number">{pct_np_fin:.0f}%</div>
            <div class="kpi-text">de la matrícula {y_fin} es no presencial
            ({n_np_fin:,.0f} estudiantes; era {pct_np_ini:.0f}% en {y_ini})</div>
        </div>
        """.replace(",", "."),
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Duración de programas: UAH vs. resto del mercado (o quien elijas)
# ---------------------------------------------------------------------------
st.header("📏 Duración de los programas (semestres)")
st.caption(
    "Columna **DURACIÓN ESTUDIO CARRERA**. Compara a la UAH contra el resto del "
    "mercado o contra instituciones específicas que elijas."
)

UAH_NOMBRE = "UNIVERSIDAD ALBERTO HURTADO"
df_dur = df[df["Año"] >= 2020].copy()

modo_comparacion = st.radio(
    "¿Contra quién quieres comparar a la UAH?",
    ["Resto del mercado (todas las demás instituciones)", "Elegir instituciones específicas"],
    horizontal=True, key="dur_modo_comp",
)

if modo_comparacion == "Elegir instituciones específicas":
    otras_instituciones = st.multiselect(
        "Elige una o más instituciones para comparar",
        sorted(df_dur[df_dur["NOMBRE INSTITUCIÓN"] != UAH_NOMBRE]["NOMBRE INSTITUCIÓN"].unique()),
        key="dur_otras_instituciones",
    )
else:
    otras_instituciones = None

# --- Serie de la UAH ---
uah_dur_year = (
    df_dur[df_dur["NOMBRE INSTITUCIÓN"] == UAH_NOMBRE]
    .groupby("Año")["DURACIÓN ESTUDIO CARRERA"].mean().reset_index()
)
uah_dur_year["Serie"] = "UAH"

series_dur = [uah_dur_year]

if modo_comparacion == "Resto del mercado (todas las demás instituciones)":
    resto_dur_year = (
        df_dur[df_dur["NOMBRE INSTITUCIÓN"] != UAH_NOMBRE]
        .groupby("Año")["DURACIÓN ESTUDIO CARRERA"].mean().reset_index()
    )
    resto_dur_year["Serie"] = "Resto del mercado"
    series_dur.append(resto_dur_year)
elif otras_instituciones:
    for inst in otras_instituciones:
        s = (
            df_dur[df_dur["NOMBRE INSTITUCIÓN"] == inst]
            .groupby("Año")["DURACIÓN ESTUDIO CARRERA"].mean().reset_index()
        )
        s["Serie"] = inst
        series_dur.append(s)

plot_dur = pd.concat(series_dur, ignore_index=True)
plot_dur["Año"] = plot_dur["Año"].astype(str)

colD1, colD2 = st.columns(2)
with colD1:
    import plotly.express as px
    fig = px.line(
        plot_dur, x="Año", y="DURACIÓN ESTUDIO CARRERA", color="Serie", markers=True,
        title="Duración promedio por año (semestres)",
        labels={"DURACIÓN ESTUDIO CARRERA": "Semestres promedio"},
    )
    for trace in fig.data:
        if trace.name == "UAH":
            trace.line.width = 4
            trace.line.color = "#C0392B"
    fig.update_xaxes(type="category")
    st.plotly_chart(fig, use_container_width=True)

with colD2:
    año_dur_pick = st.selectbox(
        "Año para el detalle de distribución", sorted(df_dur["Año"].unique(), reverse=True), key="dur_año_pick"
    )
    d_año = df_dur[df_dur["Año"] == año_dur_pick]

    if modo_comparacion == "Resto del mercado (todas las demás instituciones)":
        d_año_comp = d_año.copy()
        d_año_comp["Serie"] = d_año_comp["NOMBRE INSTITUCIÓN"].apply(
            lambda x: "UAH" if x == UAH_NOMBRE else "Resto del mercado"
        )
    else:
        insts_incluidas = [UAH_NOMBRE] + (otras_instituciones or [])
        d_año_comp = d_año[d_año["NOMBRE INSTITUCIÓN"].isin(insts_incluidas)].copy()
        d_año_comp["Serie"] = d_año_comp["NOMBRE INSTITUCIÓN"].apply(
            lambda x: "UAH" if x == UAH_NOMBRE else x
        )

    fig = px.box(
        d_año_comp, x="Serie", y="DURACIÓN ESTUDIO CARRERA", color="Serie",
        title=f"Distribución de duración por programa — {año_dur_pick}",
        points="all",
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# --- Tabla resumen ---
st.markdown("##### Resumen estadístico por serie")
resumen_dur = plot_dur.groupby("Serie")["DURACIÓN ESTUDIO CARRERA"].agg(
    Promedio="mean", Mediana="median", Mínimo="min", Máximo="max"
).round(2).reset_index()
st.dataframe(resumen_dur, use_container_width=True, hide_index=True)

st.markdown("---")

st.caption("Todos los gráficos de esta sección consideran los años 2020 en adelante.")

df_2020 = df[df["Año"] >= 2020]

tab1, tab2, tab3 = st.tabs(["Por tipo de institución", "Por modalidad", "Por área del conocimiento"])

with tab1:
    inst_year = df_2020.groupby(["Año", "CLASIFICACIÓN INSTITUCIÓN NIVEL 1"])["TOTAL MATRÍCULA"].sum().reset_index()
    inst_year["Año"] = inst_year["Año"].astype(str)
    import plotly.express as px
    fig = px.bar(
        inst_year, x="Año", y="TOTAL MATRÍCULA", color="CLASIFICACIÓN INSTITUCIÓN NIVEL 1",
        title="Matrícula por tipo de institución, año a año (2020–2025)", barmode="stack",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_xaxes(type="category")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    import plotly.express as px
    modal_year = df_2020.groupby(["Año", "MODALIDAD"])["TOTAL MATRÍCULA"].sum().reset_index()
    modal_year["Año"] = modal_year["Año"].astype(str)
    fig = px.bar(
        modal_year, x="Año", y="TOTAL MATRÍCULA", color="MODALIDAD",
        title="Matrícula por modalidad, año a año (2020–2025)", barmode="stack",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_xaxes(type="category")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    import plotly.express as px
    area_year = df_2020.groupby(["Año", "ÁREA DEL CONOCIMIENTO"])["TOTAL MATRÍCULA"].sum().reset_index()
    area_year["Año"] = area_year["Año"].astype(str)
    areas_sel = st.multiselect(
        "Áreas a mostrar", sorted(df_2020["ÁREA DEL CONOCIMIENTO"].dropna().unique()),
        default=sorted(df_2020["ÁREA DEL CONOCIMIENTO"].dropna().unique()), key="areas_extra"
    )
    fig = px.line(
        area_year[area_year["ÁREA DEL CONOCIMIENTO"].isin(areas_sel)],
        x="Año", y="TOTAL MATRÍCULA", color="ÁREA DEL CONOCIMIENTO", markers=True,
        title="Matrícula por área del conocimiento, año a año (2020–2025)",
    )
    fig.update_xaxes(type="category")
    st.plotly_chart(fig, use_container_width=True)

# ===========================================================================
# NUEVA SECCIÓN: OPORTUNIDADES PARA PSICOLOGÍA
# ===========================================================================
st.markdown("---")
st.header("🧠 Oportunidades para la Facultad de Psicología")
st.caption(
    "Análisis con **matrícula real** (no solo vacantes ofrecidas). El catálogo "
    "actual de la UAH considera todos sus programas de Psicología **hasta 2025** "
    "(el último año con datos de matrícula)."
)


def normalizar_texto(texto):
    texto = str(texto).lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


patron_psico = st.text_input(
    "Patrón de búsqueda en el nombre del programa (regex, separado por '|')",
    value="PSICOLOG|PSICOANALISIS|PSICOTERAPIA|NEUROPSICOLOG|SALUD MENTAL",
    key="psico_patron_matricula",
)

# ---------------------------------------------------------------------------
# Catálogo REAL de la UAH (2025), curado manualmente — el archivo SIES
# demostró estar incompleto/desactualizado específicamente para la UAH.
# ---------------------------------------------------------------------------
UAH_PSICO_REAL_2025 = pd.DataFrame([
    {"Programa": "Diplomado en Intervenciones en Psicología Perinatal en Chile y Latinoamérica", "Matrícula 2025": 15},
    {"Programa": "Diplomado Pasantía en Práctica Clínica Supervisada en Psicología", "Matrícula 2025": 2},
    {"Programa": "Postítulo en Neuropsicología Clínica", "Matrícula 2025": 17},
    {"Programa": "Postítulo en Psicoterapia Sistémica Relacional: Fundamentos y Estrategias para una Clínica del Cambio", "Matrícula 2025": 14},
])
UAH_MATRICULA_PSICO_2025_REAL = int(UAH_PSICO_REAL_2025["Matrícula 2025"].sum())

psico_hist = df[df["NOMBRE CARRERA"].str.contains(patron_psico, case=False, na=False, regex=True)].copy()
psico_hist = psico_hist[psico_hist["Año"] <= 2025]

if psico_hist.empty:
    st.warning("No se encontraron programas con ese patrón de búsqueda.")
else:
    # Mercado SIN la UAH (para no mezclar los datos poco confiables de SIES con los reales)
    mercado_sin_uah = psico_hist[psico_hist["NOMBRE INSTITUCIÓN"] != UAH_NOMBRE]

    st.markdown("---")
    st.subheader("📋 Catálogo real de la UAH en Psicología (2025, confirmado)")
    st.dataframe(UAH_PSICO_REAL_2025, use_container_width=True, hide_index=True)
    st.caption(f"**Matrícula total real UAH en Psicología, 2025: {UAH_MATRICULA_PSICO_2025_REAL} estudiantes.**")

    st.markdown("---")
    st.subheader("📈 Evolución del mercado completo de Psicología (matrícula real)")
    mercado_psico = mercado_sin_uah.groupby("Año").agg(
        Programas=("CÓDIGO CARRERA", "nunique"),
        Instituciones=("NOMBRE INSTITUCIÓN", "nunique"),
        Matrícula=("TOTAL MATRÍCULA", "sum"),
    ).reset_index()
    mercado_psico_2020 = mercado_psico[mercado_psico["Año"] >= 2020].copy()
    mercado_psico_2020["Año"] = mercado_psico_2020["Año"].astype(str)
    st.caption("Excluye a la UAH (que usa el catálogo real de arriba, no los datos de SIES).")

    colm1, colm2, colm3 = st.columns(3)
    with colm1:
        fig = px.line(mercado_psico_2020, x="Año", y="Programas", markers=True, title="N° de programas (resto del mercado)")
        fig.update_xaxes(type="category")
        st.plotly_chart(fig, use_container_width=True)
    with colm2:
        fig = px.line(mercado_psico_2020, x="Año", y="Instituciones", markers=True, title="N° de instituciones (resto del mercado)",
                      color_discrete_sequence=["#27AE60"])
        fig.update_xaxes(type="category")
        st.plotly_chart(fig, use_container_width=True)
    with colm3:
        fig = px.bar(mercado_psico_2020, x="Año", y="Matrícula", title="Matrícula total (resto del mercado)",
                    color_discrete_sequence=[NARANJA])
        fig.update_xaxes(type="category")
        st.plotly_chart(fig, use_container_width=True)

    mercado_2025 = mercado_psico[mercado_psico["Año"] == 2025]["Matrícula"].iloc[0] if 2025 in mercado_psico["Año"].values else 0
    c1, c2 = st.columns(2)
    c1.metric("Matrícula UAH en Psicología (2025, real)", UAH_MATRICULA_PSICO_2025_REAL)
    c2.metric("Matrícula resto del mercado (2025, SIES)", int(mercado_2025))

    st.markdown("---")
    st.subheader("🔍 Brechas temáticas: palabras clave validadas por el mercado que la UAH no cubre")
    st.caption(
        "Se cuentan las palabras clave de los nombres de programas de **2025**, "
        "en cuántas instituciones distintas aparece cada una, y si la UAH la "
        "cubre en su catálogo histórico."
    )
    min_inst_psico = st.slider("Mínimo de instituciones para considerar una temática validada", 2, 10, 3, key="psico_min_inst_mat")

    d_2025 = mercado_sin_uah[mercado_sin_uah["Año"] == 2025].copy()
    d_2025["nombre_norm"] = d_2025["NOMBRE CARRERA"].apply(normalizar_texto)

    stop_psico = [
        "de", "la", "el", "en", "y", "a", "los", "las", "del", "para", "con", "un", "una", "por", "su", "al", "o", "e", "que",
        "diplomado", "diploma", "postitulo", "curso", "programa", "nivel",
        "psicologia", "psicologico", "psicologica", "psicologicos", "psicologicas",
        "psicoanalisis", "psicoterapia", "neuropsicologia", "neuropsicologica",
        "clinica", "fundamentos", "estrategias", "desde",
    ]
    tema_instituciones = {}
    tema_programas = {}
    tema_matricula = {}
    for _, row in d_2025.iterrows():
        palabras = [w for w in row["nombre_norm"].split() if w not in stop_psico and len(w) > 3]
        for w in set(palabras):
            tema_instituciones.setdefault(w, set()).add(row["NOMBRE INSTITUCIÓN"])
            tema_programas.setdefault(w, set()).add(row["CÓDIGO CARRERA"])
            tema_matricula[w] = tema_matricula.get(w, 0) + row["TOTAL MATRÍCULA"]

    tema_df = pd.DataFrame([
        {
            "Tema": k,
            "N° instituciones": len(tema_instituciones[k]),
            "N° programas (ofertas)": len(tema_programas[k]),
            "Matrícula 2025": int(tema_matricula[k]),
        }
        for k in tema_instituciones
    ]).sort_values("N° instituciones", ascending=False)

    uah_texto_psico = " ".join(UAH_PSICO_REAL_2025["Programa"].apply(normalizar_texto))
    uah_palabras_psico = set(uah_texto_psico.split())
    tema_df["¿UAH lo cubre?"] = tema_df["Tema"].apply(lambda t: "Sí" if t in uah_palabras_psico else "No")
    tema_df_completo = tema_df.copy()
    tema_df = tema_df[tema_df["N° instituciones"] >= min_inst_psico]

    fig = px.bar(
        tema_df.head(20).sort_values("N° instituciones"),
        x="N° instituciones", y="Tema", orientation="h", color="¿UAH lo cubre?",
        color_discrete_map={"Sí": "#27AE60", "No": "#C0392B"},
        title="Temáticas más frecuentes en el mercado de Psicología — 2025",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(tema_df, use_container_width=True, hide_index=True, height=300)

    st.markdown("---")
    st.subheader("🔒 Temáticas ya muy cubiertas por el mercado")
    st.caption(
        "Temáticas más saturadas en 2025, sin filtrar por si la UAH la tiene o "
        "no — es la vista de saturación del mercado completo."
    )
    colsat1, colsat2 = st.columns(2)
    with colsat1:
        metrica_sat = st.selectbox(
            "Ordenar saturación por",
            ["N° programas (ofertas)", "N° instituciones", "Matrícula 2025"],
            index=0, key="psico_metrica_saturadas",
        )
    with colsat2:
        n_saturadas = st.slider(
            "N° de temáticas a mostrar", 5, 30, 10, key="psico_n_saturadas",
        )
    top_saturadas = tema_df_completo.sort_values(metrica_sat, ascending=False).head(n_saturadas)

    fig = px.bar(
        top_saturadas.sort_values(metrica_sat),
        x=metrica_sat, y="Tema", orientation="h", color="¿UAH lo cubre?",
        color_discrete_map={"Sí": "#27AE60", "No": "#C0392B"},
        title=f"Top {n_saturadas} temáticas más saturadas del mercado de Psicología — 2025 (por {metrica_sat})",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(top_saturadas, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🚨 5 focos priorizados: los gaps más grandes detectados")
    st.caption(
        "Se combinan palabras clave relacionadas en 5 temáticas de negocio "
        "concretas (no palabras sueltas), ordenadas de mayor a menor matrícula "
        "de mercado en 2025. Ninguna está cubierta hoy por el catálogo de la UAH."
    )

    FOCOS = {
        "🧠 Salud Mental": "SALUD MENTAL",
        "⚖️ Psicología Jurídica / Forense": "JURIDIC|FORENSE|PERITAJE",
        "🧩 Psicoterapia Cognitivo-Constructivista": "CONSTRUCTIVISTA|COGNITIVO CONDUCTUAL",
        "👶 Evaluación e Intervención Infanto-Juvenil": "INFANTO|EVALUACION.*?(?:INFANTIL|JUVENIL|NI(?:Ñ|N)O)",
        "🏃 Psicología del Deporte": "PSICOLOGIA DEL DEPORTE|PSICOLOGIA APLICADA A LA ACTIVIDAD FISICA",
    }

    # Cobertura real de la UAH por foco, confirmada manualmente contra el catálogo
    # y las descripciones oficiales de postgrados.uahurtado.cl (no vía SIES, que
    # no tiene estos programas de la UAH registrados).
    FOCOS_UAH_COBERTURA = {
        "🧠 Salud Mental": (
            "Parcial. La UAH tiene 'Diplomado en Intervenciones en Psicología "
            "Perinatal', cuya bajada oficial es 'Salud Mental Perinatal' — pero "
            "no cubre los sub-nichos de mayor volumen (infanto-juvenil, laboral, "
            "DDHH, personas mayores)."
        ),
        "⚖️ Psicología Jurídica / Forense": "No cubierto — sin programas relacionados en el catálogo real de la UAH.",
        "🧩 Psicoterapia Cognitivo-Constructivista": "No cubierto — sin programas relacionados en el catálogo real de la UAH.",
        "👶 Evaluación e Intervención Infanto-Juvenil": "No cubierto — sin programas relacionados en el catálogo real de la UAH.",
        "🏃 Psicología del Deporte": "No cubierto — sin programas relacionados en el catálogo real de la UAH.",
    }

    resumen_focos = []
    for nombre_foco, patron_foco in FOCOS.items():
        d_foco = mercado_sin_uah[
            (mercado_sin_uah["NOMBRE CARRERA"].str.contains(patron_foco, case=False, na=False, regex=True))
            & (mercado_sin_uah["Año"] <= 2025)
        ]
        d_foco_2025 = d_foco[d_foco["Año"] == 2025]
        resumen_focos.append({
            "Foco": nombre_foco,
            "Instituciones 2025": d_foco_2025["NOMBRE INSTITUCIÓN"].nunique(),
            "Matrícula 2025": int(d_foco_2025["TOTAL MATRÍCULA"].sum()),
        })
    resumen_focos_df = pd.DataFrame(resumen_focos).sort_values("Matrícula 2025", ascending=False)
    resumen_focos_df["Etiqueta"] = resumen_focos_df["Matrícula 2025"].apply(
        lambda v: f"{v:,}".replace(",", ".")
    )

    fig = px.bar(
        resumen_focos_df.sort_values("Matrícula 2025"),
        x="Matrícula 2025", y="Foco", orientation="h",
        color="Instituciones 2025", color_continuous_scale="Reds",
        text="Etiqueta",
        title="Los 5 focos, ordenados por matrícula de mercado 2025 (resto del mercado, sin UAH)",
    )
    fig.update_traces(textposition="inside", insidetextanchor="end", textfont=dict(color="black", size=13))
    fig.update_coloraxes(colorbar_tickformat=",d")
    st.plotly_chart(fig, use_container_width=True)

    for nombre_foco in resumen_focos_df["Foco"]:
        patron_foco = FOCOS[nombre_foco]
        with st.expander(f"{nombre_foco} — ver detalle"):
            f_hist = mercado_sin_uah[
                (mercado_sin_uah["NOMBRE CARRERA"].str.contains(patron_foco, case=False, na=False, regex=True))
                & (mercado_sin_uah["Año"] <= 2025)
            ]
            f_year = f_hist.groupby("Año").agg(
                Programas=("CÓDIGO CARRERA", "nunique"),
                Instituciones=("NOMBRE INSTITUCIÓN", "nunique"),
                Matrícula=("TOTAL MATRÍCULA", "sum"),
            ).reset_index()
            f_year_2020 = f_year[f_year["Año"] >= 2020].copy()
            f_year_2020["Año"] = f_year_2020["Año"].astype(str)

            colf1, colf2 = st.columns(2)
            with colf1:
                fig = px.line(
                    f_year_2020, x="Año", y=["Programas", "Instituciones"], markers=True,
                    title=f"{nombre_foco}: N° de programas e instituciones (resto del mercado)",
                    labels={"value": "", "variable": ""},
                )
                fig.update_xaxes(type="category")
                st.plotly_chart(fig, use_container_width=True)
            with colf2:
                fig = px.bar(
                    f_year_2020, x="Año", y="Matrícula", title=f"{nombre_foco}: matrícula total por año (resto del mercado)",
                    color_discrete_sequence=["#8E44AD"],
                )
                fig.update_xaxes(type="category")
                st.plotly_chart(fig, use_container_width=True)

            cobertura = FOCOS_UAH_COBERTURA[nombre_foco]
            if cobertura.startswith("Parcial"):
                st.warning(f"📌 Cobertura UAH: {cobertura}")
            else:
                st.error(f"📌 Cobertura UAH: {cobertura}")

            st.markdown(f"**Instituciones que ofrecen {nombre_foco} — 2025**")
            f_2025_detalle = f_hist[f_hist["Año"] == 2025][
                ["NOMBRE INSTITUCIÓN", "NOMBRE CARRERA", "TOTAL MATRÍCULA"]
            ].sort_values("TOTAL MATRÍCULA", ascending=False)
            st.dataframe(f_2025_detalle, use_container_width=True, hide_index=True, height=300)

            csv_foco = f_2025_detalle.to_csv(index=False).encode("utf-8")
            st.download_button(
                f"⬇️ Descargar '{nombre_foco}' (CSV)", csv_foco,
                f"foco_{nombre_foco.split(' ',1)[-1].lower().replace(' ','_').replace('/','_')}_2025.csv",
                "text/csv", key=f"dl_{nombre_foco}",
            )

