import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

# ==========================================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================================
st.set_page_config(
    page_title="Copa Challenger - Ranking FIFA",
    page_icon="🏆",
    layout="wide"
)

# Paleta fixa por confederação -> garante que as cores nunca mudam
# entre gráficos diferentes, mesmo quando o filtro remove opções.
CORES_CONFED = {
    "UEFA": "#1f77b4",
    "CONMEBOL": "#d62728",
    "CAF": "#2ca02c",
    "AFC": "#ff7f0e",
    "CONCACAF": "#9467bd",
    "OFC": "#17becf",
}

# ==========================================================
# CARGA DE DADOS
# ==========================================================
@st.cache_data
def carregar_dados():
    # Opção 1: direto do MySQL (funciona local, não no deploy na nuvem)
    try:
        engine = create_engine(
            "mysql+pymysql://root:paulo360@localhost:3306/copa_challenger"
        )
        df = pd.read_sql("SELECT * FROM fifa_ranking", con=engine)
    except Exception:
        # Opção 2: fallback pro CSV, essencial para publicar no Streamlit Cloud
        df = pd.read_csv("fifa_ranking_2022-10-06.csv")

    df["points_change"] = df["points"] - df["previous_points"]
    df["rank_change"] = df["previous_rank"] - df["rank"]
    return df

df = carregar_dados()

# ==========================================================
# SIDEBAR - FILTROS
# ==========================================================
st.sidebar.header("🔎 Filtros")

confederacoes = sorted(df["association"].unique())
filtro_confed = st.sidebar.multiselect(
    "Confederação",
    options=confederacoes,
    default=confederacoes
)

top_n = st.sidebar.slider("Top N seleções (por rank)", 5, 50, 10)

df_filtrado = df[df["association"].isin(filtro_confed)]

if df_filtrado.empty:
    st.warning("Nenhuma confederação selecionada. Escolha ao menos uma no filtro lateral.")
    st.stop()

# ==========================================================
# HEADER + KPIs
# ==========================================================
st.title("🏆 Copa Challenger — Ranking FIFA")
st.caption("Dados: Copas 2018 e 2022 · Fonte: Kaggle (piterfm/fifa-football-world-cup)")

st.markdown("""
Este painel conta a história de como as seleções nacionais se posicionam no
ranking FIFA: quem domina, quem está subindo, quem está caindo, e como as
confederações se comparam entre si. Use os filtros à esquerda para explorar
por confederação.
""")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Seleções", f"{df_filtrado['team'].nunique()}")
col2.metric("Média de Pontos", f"{df_filtrado['points'].mean():.0f}")
col3.metric("Maior Alta", f"{df_filtrado['rank_change'].max():.0f} posições")
col4.metric("Maior Queda", f"{df_filtrado['rank_change'].min():.0f} posições")

st.divider()

# ==========================================================
# TOP N SELEÇÕES
# ==========================================================
st.subheader(f"🥇 Top {top_n} Seleções (por Rank)")

lider = df_filtrado.nsmallest(1, "rank").iloc[0]
st.markdown(f"""
**{lider['team']}** lidera o ranking entre as confederações selecionadas, com
**{lider['points']:.0f} pontos**. O gráfico abaixo mostra como as demais
seleções do topo se distribuem — repare na concentração de países da mesma
confederação nas primeiras posições, um indício da força regional no futebol.
""")

top_selecoes = df_filtrado.nsmallest(top_n, "rank")
fig_top = px.bar(
    top_selecoes.sort_values("points"),
    x="points", y="team",
    color="association",
    color_discrete_map=CORES_CONFED,
    orientation="h",
    labels={"points": "Pontos", "team": "Seleção", "association": "Confederação"},
)
st.plotly_chart(fig_top, use_container_width=True)

# ==========================================================
# DISTRIBUIÇÃO DE PONTOS + BOXPLOT POR CONFEDERAÇÃO
# ==========================================================
st.subheader("📊 Como os pontos se distribuem")

media_por_confed = df_filtrado.groupby("association")["points"].mean().sort_values(ascending=False)
confed_top = media_por_confed.index[0]
confed_baixo = media_por_confed.index[-1]

st.markdown(f"""
A distribuição geral de pontos é assimétrica (poucas seleções concentram
pontuações muito altas). Ao comparar confederações, **{confed_top}** tem a
maior média de pontos (**{media_por_confed.iloc[0]:.0f}**), enquanto
**{confed_baixo}** tem a menor (**{media_por_confed.iloc[-1]:.0f}**) — uma
diferença que reflete o nível de competitividade entre as regiões.
""")

col_a, col_b = st.columns(2)

with col_a:
    fig_hist = px.histogram(
        df_filtrado, x="points", nbins=30, marginal="box",
        labels={"points": "Pontos"}
    )
    fig_hist.update_layout(title="Distribuição de Pontos")
    st.plotly_chart(fig_hist, use_container_width=True)

with col_b:
    fig_box = px.box(
        df_filtrado, x="association", y="points", color="association",
        color_discrete_map=CORES_CONFED,
        labels={"association": "Confederação", "points": "Pontos"}
    )
    fig_box.update_layout(
        title="Pontos por Confederação",
        yaxis_range=[df_filtrado["points"].min() - 50, df_filtrado["points"].max() + 50],
        showlegend=False
    )
    st.plotly_chart(fig_box, use_container_width=True)

# ==========================================================
# RANK ATUAL VS ANTERIOR
# ==========================================================
st.subheader("🔄 Rank Atual vs Rank Anterior")

subiu = int((df_filtrado["rank_change"] > 0).sum())
caiu = int((df_filtrado["rank_change"] < 0).sum())
estavel = int((df_filtrado["rank_change"] == 0).sum())

st.markdown(f"""
A maioria das seleções segue próxima à linha diagonal (tracejada em vermelho),
indicando estabilidade entre uma atualização e outra do ranking. Neste recorte,
**{subiu} seleções subiram**, **{caiu} caíram** e **{estavel} permaneceram
estáveis**. Pontos bem distantes da diagonal indicam mudanças bruscas de
posição — vale investigar essas seleções na tabela abaixo.
""")

fig_scatter = px.scatter(
    df_filtrado, x="previous_rank", y="rank",
    color="association", hover_name="team",
    color_discrete_map=CORES_CONFED,
    labels={"previous_rank": "Rank Anterior", "rank": "Rank Atual", "association": "Confederação"}
)
fig_scatter.add_shape(
    type="line", x0=1, y0=1, x1=211, y1=211,
    line=dict(color="red", dash="dash")
)
fig_scatter.update_layout(legend_title_text="Confederação")
st.plotly_chart(fig_scatter, use_container_width=True)

# ==========================================================
# MAIORES ALTAS E QUEDAS
# ==========================================================
st.subheader("📈 Quem mais subiu e quem mais caiu")

maior_alta = df_filtrado.nlargest(1, "rank_change").iloc[0]
maior_queda = df_filtrado.nsmallest(1, "rank_change").iloc[0]

st.markdown(f"""
**{maior_alta['team']}** teve a maior alta, subindo
**{maior_alta['rank_change']:.0f} posições** (de {maior_alta['previous_rank']:.0f}ª
para {maior_alta['rank']:.0f}ª). Já **{maior_queda['team']}** teve a maior
queda, perdendo **{abs(maior_queda['rank_change']):.0f} posições** (de
{maior_queda['previous_rank']:.0f}ª para {maior_queda['rank']:.0f}ª).
""")

col_c, col_d = st.columns(2)

with col_c:
    st.markdown("**Maiores Altas**")
    st.dataframe(
        df_filtrado.nlargest(10, "rank_change")[["team", "rank", "previous_rank", "rank_change"]],
        hide_index=True, use_container_width=True
    )

with col_d:
    st.markdown("**Maiores Quedas**")
    st.dataframe(
        df_filtrado.nsmallest(10, "rank_change")[["team", "rank", "previous_rank", "rank_change"]],
        hide_index=True, use_container_width=True
    )

# ==========================================================
# CONCLUSÕES
# ==========================================================
st.divider()
st.subheader("📝 Conclusões")

st.markdown(f"""
- **Concentração de poder**: as primeiras posições do ranking são dominadas
  por seleções da {confed_top}, evidenciando a força competitiva dessa
  confederação frente às demais.
- **Disparidade regional**: a diferença de média de pontos entre
  {confed_top} ({media_por_confed.iloc[0]:.0f}) e {confed_baixo}
  ({media_por_confed.iloc[-1]:.0f}) mostra um desequilíbrio competitivo
  relevante entre regiões do futebol mundial.
- **Estabilidade geral, com exceções pontuais**: a maior parte das seleções
  mantém posição próxima à anterior, mas casos como {maior_alta['team']}
  (+{maior_alta['rank_change']:.0f}) e {maior_queda['team']}
  ({maior_queda['rank_change']:.0f}) mostram que mudanças bruscas acontecem
  e merecem investigação de contexto (resultados recentes, jogos decisivos, etc).
- **Próximos passos sugeridos**: cruzar esses dados com resultados de partidas
  específicas das Copas de 2018 e 2022 ajudaria a explicar *por que* essas
  variações ocorreram, e não apenas *que* elas ocorreram.
""")

# ==========================================================
# TABELA COMPLETA
# ==========================================================
st.divider()
st.subheader("📋 Tabela Completa")
st.dataframe(df_filtrado.sort_values("rank"), hide_index=True, use_container_width=True)
