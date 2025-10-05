# Conteúdo ATUALIZADO de pages/6_📊_Mapa_da_Liga.py

import streamlit as st
from utils.coc_api import generate_full_league_preview

st.set_page_config(page_title="Mapa da Liga", page_icon="📊", layout="wide")
st.title("📊 Mapa Estratégico Completo da Liga")

if 'clan_tag' not in st.session_state or not st.session_state['clan_tag']:
    st.warning("⬅️ Por favor, insira uma tag de clã na página principal para começar.")
else:
    st.warning("⚠️ **Atenção:** A geração deste mapa completo pode levar vários minutos.")

    if st.button("Gerar Mapa Completo da Liga"):
        try:
            clan_tag = st.session_state['clan_tag']
            coc_email = st.secrets["coc_email"]
            coc_password = st.secrets["coc_password"]

            with st.spinner("Espionando todos os clãs do grupo... Sente-se e pegue um café ☕"):
                # A chamada agora espera apenas 2 valores
                df_our_clan, league_preview = generate_full_league_preview(clan_tag, coc_email, coc_password)

            if league_preview is None:
                # df_our_clan terá a mensagem de erro da função
                st.error(f"Não foi possível gerar o mapa da liga: {df_our_clan}") 
            else:
                st.success("Mapa estratégico completo gerado com sucesso!")
                
                for matchup in league_preview:
                    opponent_name = matchup['opponent_name']
                    df_predicted_opponent = matchup['predicted_lineup']
                    
                    st.divider()
                    # O nome do seu clã "hardcoded" no título
                    st.header(f"Previsão: Family Br vs {opponent_name}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Nossa Escalação Atual")
                        st.dataframe(df_our_clan, hide_index=True)
                    with col2:
                        st.subheader(f"Escalação Provável de '{opponent_name}'")
                        st.dataframe(df_predicted_opponent, hide_index=True)

        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao gerar o mapa: {e}")
