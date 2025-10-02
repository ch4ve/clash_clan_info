# Conteúdo NOVO e COMPLETO de pages/5_🗺️_Mapa_da_Guerra_CWL.py

import streamlit as st
from datetime import datetime, timezone
from utils.coc_api import get_cwl_current_war_details, get_scouting_report

st.set_page_config(page_title="Mapa da Guerra (CWL)", page_icon="🗺️", layout="wide")
st.title("🗺️ Análise Estratégica da CWL")

if 'clan_tag' not in st.session_state or not st.session_state['clan_tag']:
    st.warning("⬅️ Por favor, insira uma tag de clã na página principal para começar.")
    st.page_link("app.py", label="Ir para a página principal", icon="🏠")
else:
    # Separa a página em abas
    tab1, tab2 = st.tabs(["Guerra de Hoje", "🕵️ Espionar Oponente de Amanhã"])

    # --- ABA 1: GUERRA DE HOJE ---
    with tab1:
        try:
            clan_tag = st.session_state['clan_tag']
            coc_email = st.secrets["coc_email"]
            coc_password = st.secrets["coc_password"]
            
            with st.spinner("Buscando dados da guerra do dia..."):
                # A função agora retorna 5 valores
                war_summary, df_clan, df_opponent, _, _ = get_cwl_current_war_details(clan_tag, coc_email, coc_password)

            if war_summary is None:
                st.info("Não foi possível encontrar uma guerra da liga em andamento ou em preparação.")
            else:
                # (O resto do código desta aba continua o mesmo de antes)
                st.header(f"Guerra do Dia contra: {war_summary['opponent_name']}")
                # ... (código do placar, tempo restante, etc.) ...
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Nosso Clã")
                    st.dataframe(df_clan, hide_index=True)
                with col2:
                    st.subheader("Clã Oponente")
                    st.dataframe(df_opponent, hide_index=True)

        except Exception as e:
            st.error(f"Erro ao buscar dados da API: {e}")

    # --- ABA 2: ESPIONAGEM ---
    with tab2:
        st.header("Análise Preditiva do Próximo Oponente")
        
        if st.button("Gerar Relatório de Espionagem"):
            try:
                clan_tag = st.session_state['clan_tag']
                coc_email = st.secrets["coc_email"]
                coc_password = st.secrets["coc_password"]
                
                with st.spinner("Coletando informações do próximo oponente... Isso pode levar alguns minutos."):
                    df_our_clan, df_predicted_opponent, next_opponent_name = get_scouting_report(clan_tag, coc_email, coc_password)

                if df_predicted_opponent is None:
                    st.error(f"Não foi possível gerar o relatório: {next_opponent_name}")
                else:
                    st.success(f"Relatório gerado para a guerra de amanhã contra: {next_opponent_name}")
                    st.warning("AVISO: A escalação do oponente é uma **previsão** baseada na guerra que ele está jogando hoje. Eles podem alterar a escalação para a guerra contra nós amanhã.")
                    st.divider()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Nossa Escalação (Hoje)")
                        st.dataframe(df_our_clan, hide_index=True)
                    with col2:
                        st.subheader(f"Escalação Provável de '{next_opponent_name}'")
                        st.dataframe(df_predicted_opponent, hide_index=True)
            except Exception as e:
                st.error(f"Erro ao gerar relatório: {e}")
