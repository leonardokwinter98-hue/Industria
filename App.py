import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Geomarketing Industrial | eFact",
    page_icon="🏭",
    layout="wide"
)

st.title("🎯 eFact - Inteligência de Expansão Comercial e Geomarketing")
st.markdown("Painel executivo com motor de extração e mapeamento dinâmico de indústrias no Rio Grande do Sul.")

# 2. MOTOR DE AQUISIÇÃO E FILTRAGEM DINÂMICA EM TEMPO REAL
@st.cache_data(ttl=86400) # Cache de 24 horas para otimizar a performance
def carregar_dados_dinamicos():
    # URL pública direta da base limpa de indústrias do RS (hospedada em nuvem / GitHub Raw)
    # Assim o app baixa a base atualizada em segundos sem precisar de arquivos locais no repositório.
    url_dados = "https://raw.githubusercontent.com/leonardokwinter98-hue/Industria/main/dados_industrias_efact_final.csv"
    
    try:
        df = pd.read_csv(url_dados)
    except:
        # Fallback caso a URL direta precise de ajuste
        df = pd.read_csv("https://raw.githubusercontent.com/leonardokwinter98-hue/Industria/main/dados_industrias_efact_final.csv")
        
    return df

try:
    with st.spinner("Conectando à base de dados territorial e carregando indústrias do RS..."):
        df = carregar_dados_dinamicos()
except Exception as e:
    st.error(f"Erro ao conectar com a fonte de dados remota: {e}")
    st.stop()

# 3. FILTRAGEM INTERATIVA NA BARRA LATERAL
st.sidebar.header("Filtros de Prospecção")

setores = sorted(df['subsetor_efact'].dropna().unique().tolist()) if 'subsetor_efact' in df.columns else []
setor_sel = st.sidebar.multiselect("Selecione os Setores:", setores, default=setores)

municipios = sorted(df['municipio'].dropna().unique().tolist()) if 'municipio' in df.columns else []
mun_sel = st.sidebar.multiselect("Selecione os Municípios:", municipios)

df_filtrado = df.copy()
if setor_sel and 'subsetor_efact' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['subsetor_efact'].isin(setor_sel)]
if mun_sel and 'municipio' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['municipio'].isin(mun_sel)]

# 4. MÉTRICAS EXECUTIVAS
c1, c2, c3 = st.columns(3)
c1.metric("Indústrias Alvo Mapeadas", len(df_filtrado))
c2.metric("Municípios Abrangidos", df_filtrado['municipio'].nunique() if 'municipio' in df_filtrado.columns else 0)
c3.metric("Setores Ativos", len(setor_sel))

def escolher_cor(subsetor):
    if not isinstance(subsetor, str): return 'gray'
    if 'Química' in subsetor or 'Plástico' in subsetor: return 'purple'
    elif 'Metalurgia' in subsetor: return 'red'
    elif 'Alimentos' in subsetor: return 'orange'
    elif 'Celulose' in subsetor or 'Papel' in subsetor: return 'green'
    elif 'Automotivo' in subsetor: return 'cadetblue'
    else: return 'blue'

# 5. RENDERIZAÇÃO DO MAPA
st.subheader("Mapa de Dispersão e Polos Industriais")

lat_centro, lon_centro = -30.0346, -51.2177
if not df_filtrado.empty and 'latitude' in df_filtrado.columns:
    lat_centro = df_filtrado['latitude'].mean()
    lon_centro = df_filtrado['longitude'].mean()

mapa_efact = folium.Map(location=[lat_centro, lon_centro], zoom_start=8, tiles='CartoDB positron')

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

with st.expander("Ver base de dados detalhada das indústrias filtradas"):
    colunas_mostrar = [c for c in ['cnpj', 'nome_fantasia', 'subsetor_efact', 'municipio'] if c in df_filtrado.columns]
    st.dataframe(df_filtrado[colunas_mostrar], use_container_width=True)