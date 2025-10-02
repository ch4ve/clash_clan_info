# Conteúdo da NOVA PÁGINA: pages/6_📊_Mapa_da_Liga.py

import streamlit as st
# Importamos nossa nova função "mestra"
from utils.coc_api import generate_full_league_preview

st.set_page_config(page_title="Mapa da Liga", page_icon="📊", layout="wide")
st.title("📊 Mapa Estratégico Completo da Liga")

if 'clan_tag' not in st.session_state or not st.session_state['clan_tag']:
    st.warning("⬅️ Por favor, insira uma tag de clã na página principal para começar.")
    st.page_link("app.py", label="Ir para a página principal", icon="🏠")
else:
    st.warning("⚠️ **Atenção:** A geração deste mapa completo é um processo **muito demorado**, pois precisa fazer dezenas de consultas à API. Pode levar vários minutos para carregar.")

    if st.button("Gerar Mapa Completo da Liga"):
        try:
            clan_tag = st.session_state['clan_tag']
            coc_email = st.secrets["coc_email"]
            coc_password = st.secrets["coc_password"]

            with st.spinner("Espionando todos os clãs do grupo... Sente-se e pegue um café ☕"):
                df_our_clan, league_preview = generate_full_league_preview(clan_tag, coc_email, coc_password)

            if league_preview is None:
                st.error("Não foi possível gerar o mapa da liga. Verifique se o clã está em uma CWL.")
            else:
                st.success("Mapa estratégico completo gerado com sucesso!")
                
                # Loop para exibir cada confronto
                for matchup in league_preview:
                    opponent_name = matchup['opponent_name']
                    df_predicted_opponent = matchup['predicted_lineup']
                    
                    st.divider()
                    st.header(f"Previsão: {df_our_clan['Nome'].iloc[0] if not df_our_clan.empty else 'Nosso Clã'} vs {opponent_name}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Nossa Escalação Atual")
                        st.dataframe(df_our_clan, hide_index=True)
                    with col2:
                        st.subheader(f"Escalação Provável de '{opponent_name}'")
                        st.dataframe(df_predicted_opponent, hide_index=True)

        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao gerar o mapa: {e}")
