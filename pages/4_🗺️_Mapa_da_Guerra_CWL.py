# Conteúdo COMPLETO e ATUALIZADO de pages/5_🗺️_Mapa_da_Guerra_CWL.py

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
# Importamos a função para listar os clãs
from utils.coc_api import get_cwl_current_war_details, get_cwl_group_clans

st.set_page_config(page_title="Mapa da Guerra (CWL)", page_icon="🗺️", layout="wide")
st.title("🗺️ Análise Estratégica da CWL")

if 'clan_tag' not in st.session_state or not st.session_state['clan_tag']:
    st.warning("⬅️ Por favor, insira uma tag de clã na página principal para começar.")
    st.page_link("app.py", label="Ir para a página principal", icon="🏠")
else:
    try:
        clan_tag = st.session_state['clan_tag']
        coc_email = st.secrets["coc_email"]
        coc_password = st.secrets["coc_password"]

        # --- NOVO BLOCO: LISTA DE CLÃS DO GRUPO ---
        with st.expander("📖 Ver todos os clãs do grupo da Liga"):
            with st.spinner("Buscando lista de clãs..."):
                all_clans_in_group = get_cwl_group_clans(clan_tag, coc_email, coc_password)
                
                if not all_clans_in_group:
                    st.warning("Não foi possível carregar a lista de clãs do grupo.")
                else:
                    # Cria uma lista de dicionários para o DataFrame
                    clans_list = [{'Nome do Clã': clan.name, 'Tag': clan.tag} for clan in all_clans_in_group]
                    df_clans = pd.DataFrame(clans_list)
                    st.dataframe(df_clans, hide_index=True)
        
        st.divider()

        # --- BLOCO 2: GUERRA DE HOJE (Seu Clã) ---
        st.header("Guerra de Hoje")
        
        with st.spinner("Buscando dados da sua guerra do dia..."):
            war_summary, df_clan, df_opponent, _, _ = get_cwl_current_war_details(clan_tag, coc_email, coc_password)

        if war_summary is None:
            st.info("Não foi possível encontrar a sua guerra da liga em andamento ou em preparação.")
        else:
            # (O código para exibir sua guerra do dia continua o mesmo)
            st.subheader(f"Sua Guerra contra: {war_summary['opponent_name']}")
            # ... (código do tempo restante, etc.) ...
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(f"Clã: {war_summary['clan_name']}")
                st.dataframe(df_clan, hide_index=True)
            with col2:
                st.subheader(f"Oponente: {war_summary['opponent_name']}")
                st.dataframe(df_opponent, hide_index=True)

        st.divider()

        # --- BLOCO 3: ESPIONAGEM ESPECÍFICA (COM MENU DE SELEÇÃO) ---
        st.header("🕵️ Espionar Guerra de Outro Clã da Liga")

        if not all_clans_in_group:
            st.warning("Lista de clãs indisponível para espionagem.")
        else:
            # Cria um mapa de Nome -> Tag e filtra para mostrar apenas os oponentes
            opponent_map = {clan.name: clan.tag for clan in all_clans_in_group if clan.tag != clan_tag}
            
            # Cria o menu de seleção com os nomes dos oponentes
            selected_opponent_name = st.selectbox(
                "Selecione um clã do seu grupo para espionar:",
                options=opponent_map.keys()
            )

            if st.button("Buscar Guerra Específica"):
                if selected_opponent_name:
                    # Pega a tag correspondente ao nome selecionado
                    scout_tag = opponent_map[selected_opponent_name]
                    
                    with st.spinner(f"Buscando a guerra atual de '{selected_opponent_name}'..."):
                        scout_summary, scout_df1, scout_df2, _, _ = get_cwl_current_war_details(scout_tag, coc_email, coc_password)
                    
                    if scout_summary is None:
                        st.error(f"Não foi possível encontrar uma guerra em andamento para o clã '{selected_opponent_name}'.")
                    else:
                        st.subheader(f"Resultado da Espionagem: {scout_summary['clan_name']} vs {scout_summary['opponent_name']}")
                        
                        col3, col4 = st.columns(2)
                        with col3:
                            st.subheader(f"Clã: {scout_summary['clan_name']}")
                            st.dataframe(scout_df1, hide_index=True)
                        with col4:
                            st.subheader(f"Oponente: {scout_summary['opponent_name']}")
                            st.dataframe(scout_df2, hide_index=True)

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")
