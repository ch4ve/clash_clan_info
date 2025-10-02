# Conteúdo CORRIGIDO de pages/5_🗺️_Mapa_da_Guerra_CWL.py

import streamlit as st
from datetime import datetime, timezone
from utils.coc_api import get_cwl_current_war_details

st.set_page_config(page_title="Mapa da Guerra (CWL)", page_icon="🗺️", layout="wide")
st.title("🗺️ Mapa da Guerra do Dia (CWL)")

if 'clan_tag' not in st.session_state or not st.session_state['clan_tag']:
    st.warning("⬅️ Por favor, insira uma tag de clã na página principal para começar.")
    st.page_link("app.py", label="Ir para a página principal", icon="🏠")
else:
    try:
        clan_tag = st.session_state['clan_tag']
        coc_email = st.secrets["coc_email"]
        coc_password = st.secrets["coc_password"]

        with st.spinner("Buscando dados da guerra do dia..."):
            war_summary, df_clan, df_opponent = get_cwl_current_war_details(clan_tag, coc_email, coc_password)

        if war_summary is None:
            st.info("Não foi possível encontrar uma guerra da liga em andamento ou em preparação.")
        else:
            st.header(f"Guerra do Dia contra: {war_summary['opponent_name']}")
            
            # --- CORREÇÃO APLICADA AQUI ---
            now = datetime.now(timezone.utc)
            if war_summary['state'] == 'preparation':
                # "Avisamos" à data de início que ela está em UTC
                start_time_aware = war_summary['start_time'].time.replace(tzinfo=timezone.utc)
                tempo_restante = start_time_aware - now
                # Adiciona verificação para tempo negativo (se a guerra já começou)
                if tempo_restante.total_seconds() > 0:
                    st.info(f"Dia de Preparação! A guerra começa em: {str(tempo_restante).split('.')[0]}")
                else:
                    st.warning("A guerra está prestes a começar!")

            elif war_summary['state'] == 'inWar':
                # "Avisamos" à data de fim que ela está em UTC
                end_time_aware = war_summary['end_time'].time.replace(tzinfo=timezone.utc)
                tempo_restante = end_time_aware - now
                if tempo_restante.total_seconds() > 0:
                    st.warning(f"Guerra em Andamento! Tempo restante: {str(tempo_restante).split('.')[0]}")
                else:
                    st.success("A guerra acabou de terminar!")
            else:
                st.success(f"Guerra Finalizada! ({war_summary['state']})")

            # --- VISUALIZAÇÃO LADO A LADO ---
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Nosso Clã")
                st.dataframe(df_clan, hide_index=True)
            with col2:
                st.subheader("Clã Oponente")
                st.dataframe(df_opponent, hide_index=True)
    except Exception as e:
        st.error(f"Erro ao buscar dados da API: {e}")
