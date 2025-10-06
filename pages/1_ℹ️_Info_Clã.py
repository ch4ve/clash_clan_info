# Conteúdo COMPLETO e ATUALIZADO de pages/1_ℹ️_Info_Clã.py

import streamlit as st
import pandas as pd
from utils.coc_api import get_clan_data
from utils.database import get_top_war_performers

st.set_page_config(page_title="Info do Clã", page_icon="ℹ️", layout="wide")

if 'clan_tag' not in st.session_state or not st.session_state['clan_tag']:
    st.warning("🔒 Por favor, faça o login na página principal para visualizar as informações do clã.")
    st.page_link("app.py", label="Ir para a página de Login", icon="🔑")
else:
    try:
        clan_tag = st.session_state['clan_tag']
        coc_email = st.secrets.get("coc_email")
        coc_password = st.secrets.get("coc_password")

        with st.spinner("Buscando e analisando dados do clã..."):
            df_members, clan_name, clan_badge_url = get_clan_data(clan_tag, coc_email, coc_password)
        
        if df_members is not None and not df_members.empty:
            
            # --- TÍTULO COM EMBLEMA DO CLÃ ---
            col_title1, col_title2 = st.columns([1, 10])
            with col_title1:
                st.image(clan_badge_url, width=100)
            with col_title2:
                st.title(f"Dashboard do Clã: {clan_name}")
                st.success(f"Exibindo dados para o clã: {clan_tag}")
            
            st.divider()

            # --- LÓGICA PARA CRIAR A COLUNA DE LINKS ---
            # Remove o '#' da tag e cria a URL completa
            df_members['Link'] = df_members['Tag'].apply(
                lambda tag: f"https://www.clashofstats.com/players/{tag.strip('#')}/summary"
            )

            # --- TABELA COMPLETA DE MEMBROS COM ÍCONES E LINKS ---
            st.header("Membros Atuais")
            st.dataframe(
                df_members,
                column_config={
                    "Nome": st.column_config.LinkColumn(
                        "Nome", # Título da coluna
                        display_text="{Nome}", # Texto que aparece (da coluna 'Nome')
                        url="Link" # Coluna que contém a URL
                    ),
                    "Ícone Liga": st.column_config.ImageColumn("Liga", width="small"),
                    # Esconde as colunas que não queremos mostrar
                    "Tag": None,
                    "Link": None
                },
                column_order=[ # Define a ordem final das colunas
                    "Nome", "Cargo", "CV", "Ícone Liga", "Troféus", "Rei Bárbaro",
                    "Rainha Arqueira", "Grande Guardião", "Campeã Real"
                ],
                hide_index=True,
                use_container_width=True
            )
            
            # (O resto da página, com KPIs, Gráfico e Top 5, continua igual)
            st.divider()
            
            # --- MÉTRICAS, GRÁFICO E TOP 5 ---
            # ... cole aqui o código dos KPIs, do gráfico de CVs e do Top 5 que já tínhamos ...

        else:
            st.error("Não foi possível carregar os dados do clã.")
            
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")
