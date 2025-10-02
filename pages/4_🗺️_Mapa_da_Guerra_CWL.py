# CONTEÚDO COMPLETO PARA SUBSTITUIR EM: pages/5_🗺️_Mapa_da_Guerra_CWL.py (ou o número que for)

import streamlit as st
from datetime import datetime, timezone
from utils.coc_api import get_cwl_current_war_details, get_scouting_report

st.set_page_config(page_title="Mapa da Guerra (CWL)", page_icon="🗺️", layout="wide")
st.title("🗺️ Análise Estratéggica da CWL")

if 'clan_tag' not in st.session_state or not st.session_state['clan_tag']:
    st.warning("⬅️ Por favor, insira uma tag de clã na página principal para começar.")
    st.page_link("app.py", label="Ir para a página principal", icon="🏠")
else:
    try:
        # --- BLOCO 1: GUERRA DE HOJE ---
        st.header("Guerra de Hoje")
        
        clan_tag = st.session_state['clan_tag']
        coc_email = st.secrets["coc_email"]
        coc_password = st.secrets["coc_password"]
        
        with st.spinner("Buscando dados da guerra do dia..."):
            war_summary, df_clan, df_opponent, _, _ = get_cwl_current_war_details(clan_tag, coc_email, coc_password)

        if war_summary is None:
            st.info("Não foi possível encontrar uma guerra da liga em andamento ou em preparação.")
        else:
            st.subheader(f"Guerra contra: {war_summary['opponent_name']}")
            
            now = datetime.now(timezone.utc)
            if war_summary['state'] == 'preparation':
                start_time_aware = war_summary['start_time'].time.replace(tzinfo=timezone.utc)
                tempo_restante = start_time_aware - now
                if tempo_restante.total_seconds() > 0:
                    st.info(f"Dia de Preparação! A guerra começa em: {str(tempo_restante).split('.')[0]}")
            elif war_summary['state'] == 'inWar':
                end_time_aware = war_summary['end_time'].time.replace(tzinfo=timezone.utc)
                tempo_restante = end_time_aware - now
                if tempo_restante.total_seconds() > 0:
                    st.warning(f"Guerra em Andamento! Tempo restante: {str(tempo_restante).split('.')[0]}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Nosso Clã")
                st.dataframe(df_clan, hide_index=True)
            with col2:
                st.subheader("Clã Oponente")
                st.dataframe(df_opponent, hide_index=True)

        st.divider()

        # --- BLOCO 2: GUERRA DE AMANHÃ (ESPIONAGEM) ---
        st.header("🔮 Análise Preditiva da Guerra de Amanhã")
        
        if st.button("Gerar Previsão para Amanhã"):
            with st.spinner("Coletando informações do próximo oponente... Isso pode levar alguns minutos."):
                df_our_clan, df_predicted_opponent, next_opponent_name = get_scouting_report(clan_tag, coc_email, coc_password)

            if df_predicted_opponent is None:
                st.error(f"Não foi possível gerar o relatório: {next_opponent_name}")
            elif df_predicted_opponent.empty:
                 st.success(f"Análise contra '{next_opponent_name}' concluída. Parece que é o último dia da liga!")
            else:
                st.subheader(f"Previsão da Guerra contra: {next_opponent_name}")
                st.warning("AVISO: A escalação do oponente é uma **previsão** baseada na guerra que ele está jogando hoje. Eles podem alterar a escalação para a guerra contra nós amanhã.")

                col3, col4 = st.columns(2)
                with col3:
                    st.subheader("Nossa Escalação (Hoje)")
                    st.dataframe(df_our_clan, hide_index=True)
                with col4:
                    st.subheader(f"Escalação Provável de '{next_opponent_name}'")
                    st.dataframe(df_predicted_opponent, hide_index=True)

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")
