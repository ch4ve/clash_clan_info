# Conteúdo ATUALIZADO de pages/5_🗺️_Mapa_da_Guerra_CWL.py

import streamlit as st
from datetime import datetime, timezone
# Importamos a nova função de cronograma
from utils.coc_api import get_cwl_current_war_details, get_cwl_schedule

st.set_page_config(page_title="Mapa da Guerra (CWL)", page_icon="🗺️", layout="wide")
st.title("🗺️ Mapa da Guerra do Dia (CWL)")

if 'clan_tag' not in st.session_state or not st.session_state['clan_tag']:
    st.warning("⬅️ Por favor, insira uma tag de clã na página principal para começar.")
    st.page_link("login.py", label="Ir para a página principal", icon="🏠")
else:
    try:
        clan_tag = st.session_state['clan_tag']
        coc_email = st.secrets["coc_email"]
        coc_password = st.secrets["coc_password"]

        # --- NOVO BLOCO: CRONOGRAMA DA LIGA ---
        with st.expander("📅 Ver Cronograma Completo da Liga"):
            with st.spinner("Buscando cronograma de oponentes..."):
                df_schedule = get_cwl_schedule(clan_tag, coc_email, coc_password)
                if df_schedule is not None and not df_schedule.empty:
                    st.dataframe(df_schedule, hide_index=True)
                else:
                    st.warning("Não foi possível carregar o cronograma da liga.")
        
        st.divider()

        # --- O RESTO DA PÁGINA (código que já tínhamos) ---
        with st.spinner("Buscando dados da guerra do dia..."):
            war_summary, df_clan, df_opponent = get_cwl_current_war_details(clan_tag, coc_email, coc_password)

        if war_summary is None:
            st.info("Não foi possível encontrar uma guerra da liga em andamento ou em preparação.")
        else:
            st.header(f"Guerra do Dia contra: {war_summary['opponent_name']}")
            
            now = datetime.now(timezone.utc)
            if war_summary['state'] == 'preparation':
                start_time_aware = war_summary['start_time'].time.replace(tzinfo=timezone.utc)
                tempo_restante = start_time_aware - now
                if tempo_restante.total_seconds() > 0:
                    st.info(f"Dia de Preparação! A guerra começa em: {str(tempo_restante).split('.')[0]}")
                else:
                    st.warning("A guerra está prestes a começar!")
            elif war_summary['state'] == 'inWar':
                end_time_aware = war_summary['end_time'].time.replace(tzinfo=timezone.utc)
                tempo_restante = end_time_aware - now
                if tempo_restante.total_seconds() > 0:
                    st.warning(f"Guerra em Andamento! Tempo restante: {str(tempo_restante).split('.')[0]}")
                else:
                    st.success("A guerra acabou de terminar!")
            else:
                st.success(f"Guerra Finalizada! ({war_summary['state']})")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Nosso Clã")
                st.dataframe(df_clan, hide_index=True)
            with col2:
                st.subheader("Clã Oponente")
                st.dataframe(df_opponent, hide_index=True)
    except Exception as e:
        st.error(f"Erro ao buscar dados da API: {e}")

