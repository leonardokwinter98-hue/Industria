import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Geomarketing Industrial | eFact",
    page_icon="🏭",
    layout="wide"
)

st.title("🎯 eFact - Inteligência de Expansão Comercial e Geomarketing")
st.markdown("Painel executivo de mapeamento e prospecção de indústrias no Rio Grande do Sul.")

# 2. CARREGAMENTO DOS DADOS LIMPOS
@st.cache_data
def carregar_dados():
    # Procura pelo arquivo limpo ou qualquer CSV disponível
    for arquivo in ["dados_industrias_efact_final.csv", "dados_industrias_rs.csv"]:
        if os.path.exists(arquivo):
            return pd.read_csv(arquivo)
            
    for arquivo in os.listdir("."):
        if arquivo.endswith(".csv"):
            return pd.read_csv(arquivo)
            
    raise FileNotFoundError("Nenhum arquivo CSV encontrado no repositório.")

try:
    df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()

# 3. BARRA LATERAL DE FILTROS INTELIGENTES
st.sidebar.header("Filtros de Prospecção")

# Filtro por Setor eFact
setores = sorted(df['subsetor_efact'].dropna().unique().tolist()) if 'subsetor_efact' in df.columns else []
setor_sel = st.sidebar.multiselect("Selecione os Setores:", setores, default=setores)

# Filtro por Município
municipios = sorted(df['municipio'].dropna().unique().tolist()) if 'municipio' in df.columns else []
mun_sel = st.sidebar.multiselect("Selecione os Municípios:", municipios)

# Aplicação dos filtros
df_filtrado = df.copy()
if setor_sel and 'subsetor_efact' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['subsetor_efact'].isin(setor_sel)]
if mun_sel and 'municipio' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['municipio'].isin(mun_sel)]

# 4. MÉTRICAS EXECUTIVAS NO TOPO
c1, c2, c3 = st.columns(3)
c1.metric("Indústrias Alvo Filtradas", len(df_filtrado))
c2.metric("Municípios Abrangidos", df_filtrado['municipio'].nunique() if 'municipio' in df_filtrado.columns else 0)
c3.metric("Setores Ativos", len(setor_sel))

# 5. PALETA DE CORES POR SETOR EFACT
def escolher_cor(subsetor):
    if not isinstance(subsetor, str): return 'gray'
    if 'Química' in subsetor or 'Plástico' in subsetor: return 'purple'
    elif 'Metalurgia' in subsetor: return 'red'
    elif 'Alimentos' in subsetor: return 'orange'
    elif 'Celulose' in subsetor or 'Papel' in subsetor: return 'green'
    elif 'Automotivo' in subsetor: return 'cadetblue'
    else: return 'blue'

# 6. RENDERIZAÇÃO DO MAPA INTERATIVO
st.subheader("Mapa de Dispersão e Polos Industriais")

lat_centro, lon_centro = -30.0346, -51.2177
if not df_filtrado.empty and 'latitude' in df_filtrado.columns:
    lat_centro = df_filtrado['latitude'].mean()
    lon_centro = df_filtrado['longitude'].mean()

mapa_efact = folium.Map(location=[lat_centro, lon_centro], zoom_start=8, tiles='CartoDB positron')

# Renderiza os pontos no mapa (com limite de segurança para performance web se passar de 3 mil)
df_amostra = df_filtrado.head(3000)

for _, row in df_amostra.iterrows():
    nome = str(row.get('nome_fantasia', 'Indústria'))
    if nome == 'nan' or not nome.strip(): nome = "Indústria / Matriz"
    
    setor = str(row.get('subsetor_efact', 'Indústria'))
    mun = str(row.get('municipio', 'RS'))
    cnpj = str(row.get('cnpj', 'N/D'))
    
    html_popup = f"""
    <div style="font-family: Arial; font-size: 12px; width: 230px;">
        <b>🏢 {nome}</b><br>
        <hr style="margin: 5px 0;">
        <b>Setor eFact:</b> {setor}<br>
        <b>Município:</b> {mun}<br>
        <b>CNPJ:</b> {cnpj}
    </div>
    """
    
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=4,
        color=escolher_cor(setor),
        fill=True,
        fill_color=escolher_cor(setor),
        fill_opacity=0.8,
        popup=folium.Popup(html_popup, max_width=250),
        tooltip=f"{nome} ({mun})"
    ).add_to(mapa_efact)

st_folium(mapa_efact, width=1200, height=550)

# Tabela detalhada limpa
with st.expander("Ver base de dados detalhada das indústrias filtradas"):
    colunas_mostrar = [c for c in ['cnpj', 'nome_fantasia', 'subsetor_efact', 'municipio'] if c in df_filtrado.columns]
    st.dataframe(df_filtrado[colunas_mostrar], use_container_width=True)