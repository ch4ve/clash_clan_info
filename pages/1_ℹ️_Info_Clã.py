# Conteúdo de pages/1_ℹ️_Info_Clã.py

import streamlit as st
from utils.coc_api import get_clan_data

st.set_page_config(page_title="Info do Clã", page_icon="ℹ️", layout="wide")
st.title("ℹ️ Visão Geral dos Membros")

# Verifica se uma tag de clã já foi definida na página principal
if 'clan_tag' in st.session_state and st.session_state['clan_tag']:
    try:
        # Pega a tag da memória e as credenciais dos segredos!
        clan_tag = st.session_state['clan_tag']
        coc_email = st.secrets["coc_email"]
        coc_password = st.secrets["coc_password"]

        with st.spinner("Buscando dados do clã..."):
            df_members, clan_name = get_clan_data(clan_tag, coc_email, coc_password)
            
            if not df_members.empty:
                st.success(f"Exibindo dados para o clã: {clan_name} ({clan_tag})")
                st.dataframe(df_members)
            else:
                st.error("Não foi possível carregar os dados do clã.")
    except Exception as e:
        st.error(f"Erro ao buscar dados da API: {e}")

else:
    # Se nenhuma tag foi definida, instrui o usuário a voltar
    st.warning("⬅️ Por favor, insira uma tag de clã na página principal para começar.")

    