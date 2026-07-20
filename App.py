import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import zipfile
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Geomarketing Industrial | eFact",
    page_icon="🏭",
    layout="wide"
)

st.title("🎯 eFact - Inteligência de Expansão Comercial e Geomarketing")
st.markdown("Ferramenta de mapeamento dinâmico e prospecção de indústrias no Rio Grande do Sul.")

# 2. CARREGAMENTO ROBUSTO DOS DADOS
@st.cache_data
def carregar_dados():
    nome_zip = "dados_industrias_rs.zip"
    nome_csv = "dados_industrias_rs.csv"
    
    # Se o zip existir mas o CSV não, extrai
    if os.path.exists(nome_zip) and not os.path.exists(nome_csv):
        with zipfile.ZipFile(nome_zip, 'r') as zip_ref:
            zip_ref.extractall(".")
            
    # Procura pelo CSV correto
    if os.path.exists(nome_csv):
        df = pd.read_csv(nome_csv)
    else:
        # Se houver outro csv na pasta
        csvs = [f for f in os.listdir(".") if f.endswith(".csv")]
        if csvs:
            df = pd.read_csv(csvs[0])
        else:
            raise FileNotFoundError("Nenhum arquivo CSV encontrado.")
            
    # Padroniza nomes de colunas essenciais se necessário
    if 'lat' in df.columns and 'latitude' not in df.columns:
        df['latitude'] = df['lat']
    if 'lon' in df.columns and 'longitude' not in df.columns:
        df['longitude'] = df['lon']
        
    return df

try:
    df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()

# 3. FILTROS NA BARRA LATERAL COM TRATAMENTO DE SEGURANÇA
st.sidebar.header("Filtros de Prospecção")

# Identifica dinamicamente a coluna de setor/subsetor
col_setor = None
for c in ['subsetor_efact', 'subst_ef', 'cnae_fiscal_principal', 'setor']:
    if c in df.columns:
        col_setor = c
        break

if col_setor:
    setores = sorted(df[col_setor].dropna().astype(str).unique().tolist())
    setor_sel = st.sidebar.multiselect("Selecione os Setores:", setores, default=setores[:5] if len(setores)>5 else setores)
else:
    setor_sel = []

# Identifica dinamicamente a coluna de município
col_mun = None
for c in ['municipio', 'nome_municipio', 'mun']:
    if c in df.columns:
        col_mun = c
        break

if col_mun:
    municipios = sorted(df[col_mun].dropna().astype(str).unique().tolist())
    mun_sel = st.sidebar.multiselect("Selecione os Municípios:", municipios)
else:
    mun_sel = []

# Aplica os filtros
df_filtrado = df.copy()
if setor_sel and col_setor:
    df_filtrado = df_filtrado[df_filtrado[col_setor].astype(str).isin(setor_sel)]
if mun_sel and col_mun:
    df_filtrado = df_filtrado[df_filtrado[col_mun].astype(str).isin(mun_sel)]

# Limita a exibição no mapa se houver excesso de pontos para travar o navegador
if len(df_filtrado) > 5000:
    st.sidebar.warning("Muitos pontos filtrados. Exibindo uma amostra de 5.000 para melhor performance.")
    df_filtrado = df_filtrado.head(5000)

# 4. MÉTRICAS EXECUTIVAS
c1, c2, c3 = st.columns(3)
c1.metric("Indústrias Filtradas para Abordagem", len(df_filtrado))
c2.metric("Municípios Abrangidos", df_filtrado[col_mun].nunique() if col_mun in df_filtrado.columns else 0)
c3.metric("Setores Ativos", len(setor_sel) if col_setor else 0)

# 5. RENDERIZAÇÃO DO MAPA
st.subheader("Mapa de Dispersão e Polos Industriais")

lat_centro, lon_centro = -30.0346, -51.2177
if not df_filtrado.empty and 'latitude' in df_filtrado.columns and 'longitude' in df_filtrado.columns:
    # Remove valores nulos de coordenadas geograficas
    df_filtrado = df_filtrado.dropna(subset=['latitude', 'longitude'])
    if not df_filtrado.empty:
        lat_centro = df_filtrado['latitude'].mean()
        lon_centro = df_filtrado['longitude'].mean()

mapa_efact = folium.Map(location=[lat_centro, lon_centro], zoom_start=8, tiles='CartoDB positron')

for _, row in df_filtrado.iterrows():
    nome = str(row.get('nome_fantasia', row.get('nome_fnt', 'Indústria')))
    if nome == 'nan' or not nome.strip(): 
        nome = "Indústria / Matriz"
        
    setor_val = str(row.get(col_setor, 'Indústria')) if col_setor else 'Indústria'
    mun_val = str(row.get(col_mun, 'RS')) if col_mun else 'RS'
    cnpj_val = str(row.get('cnpj', 'N/D'))
    
    html_popup = f"""
    <div style="font-family: Arial; font-size: 12px; width: 220px;">
        <b>🏢 {nome}</b><br>
        <hr style="margin: 5px 0;">
        <b>Setor:</b> {setor_val}<br>
        <b>Município:</b> {mun_val}<br>
        <b>CNPJ:</b> {cnpj_val}
    </div>
    """
    
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=4,
        color='red',
        fill=True,
        fill_color='red',
        fill_opacity=0.7,
        popup=folium.Popup(html_popup, max_width=250),
        tooltip=f"{nome} ({mun_val})"
    ).add_to(mapa_efact)

st_folium(mapa_efact, width=1200, height=550)

# Tabela detalhada
with st.expander("Ver base de dados detalhada das indústrias filtradas"):
    st.dataframe(df_filtrado, use_container_width=True)