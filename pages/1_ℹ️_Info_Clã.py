import streamlit as st
import pandas as pd
from utils.coc_api import get_clan_data

st.set_page_config(page_title="Info do Clã", page_icon="ℹ️", layout="wide")

if 'clan_tag' not in st.session_state or not st.session_state['clan_tag']:
    st.warning("🔒 Por favor, faça o login na página principal para visualizar as informações do clã.")
    st.page_link("app.py", label="Ir para a página de Login", icon="🔑")
else:
    try:
        clan_tag = st.session_state['clan_tag']
        coc_email = st.secrets.get("coc_email")
        coc_password = st.secrets.get("coc_password")

        # --- LÓGICA DE CACHE MANUAL ---
        # Verifica se os dados JÁ estão salvos na memória para este clã específico.
        # Se não estiverem (ou se o clã mudou), buscamos na API.
        if 'clan_data_cache' not in st.session_state or st.session_state.get('cached_clan_tag') != clan_tag:
            with st.spinner("Buscando e analisando dados do clã (Isso acontece apenas uma vez)..."):
                df_members, clan_name, clan_badge_url = get_clan_data(clan_tag, coc_email, coc_password)
                
                if df_members is not None and not df_members.empty:
                    # Adiciona a coluna de seleção ao DataFrame antes de salvar
                    if "Selecionar" not in df_members.columns:
                        df_members.insert(0, "Selecionar", False)
                    
                    # Cria os links
                    if 'Tag' in df_members.columns:
                        df_members['Link'] = df_members['Tag'].apply(lambda tag: f"https://www.clashofstats.com/players/{tag.strip('#')}/summary")

                    # Salva tudo no session_state
                    st.session_state['clan_data_cache'] = {
                        'df': df_members,
                        'name': clan_name,
                        'badge': clan_badge_url
                    }
                    st.session_state['cached_clan_tag'] = clan_tag
                else:
                    st.error("Não foi possível carregar os dados do clã.")
                    st.stop() # Para a execução se falhar

        # --- RECUPERA OS DADOS DA MEMÓRIA ---
        # A partir daqui, usamos APENAS os dados que estão no cache, sem chamar a API.
        cache = st.session_state['clan_data_cache']
        df_members = cache['df']
        clan_name = cache['name']
        clan_badge_url = cache['badge']
        
        # --- TÍTULO COM EMBLEMA DO CLÃ ---
        col_title1, col_title2 = st.columns([1, 10])
        with col_title1:
            st.image(clan_badge_url, width=100)
        with col_title2:
            st.title(f"Dashboard do Clã: {clan_name}")
            st.success(f"Exibindo dados para o clã: {clan_tag}")
        
        st.divider()

        # --- BLOCO DOS KPIs (MÉTRICAS) ---
        st.header("Métricas Principais do Clã")
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1
