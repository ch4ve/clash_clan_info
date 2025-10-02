# Novo conteúdo de app.py (Página de Boas-vindas)

import streamlit as st
from utils.loop_manager import loop_manager # <-- ADICIONE ESTA LINHA
st.set_page_config(
    page_title="Clash Dashboard",
    page_icon="⚔️",
    layout="centered"
)

# --- CONTEÚDO DA PÁGINA ---

st.title("Bem-vindo ao Clash Dashboard!")

# Exibe a imagem que você enviou
st.image("search_clans.png")

st.header("Qual clã você deseja analisar?")

# Campo para o usuário inserir a tag do clã
clan_tag = st.text_input("Insira a tag do clã ", value="#9RG00UY9")

if st.button("Analisar Clã"):
    if clan_tag:
        # Salva a tag na memória da sessão para as outras páginas usarem
        st.session_state['clan_tag'] = clan_tag
        
        # Redireciona o usuário para a primeira página de informações
        st.switch_page("pages/1_ℹ️_Info_Clã.py")
    else:

        st.error("Por favor, insira uma tag de clã.")

