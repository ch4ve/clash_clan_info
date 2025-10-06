# Conteúdo ATUALIZADO de pages/1_ℹ️_Info_Clã.py (com placeholder)

import streamlit as st
import pandas as pd
from utils.coc-api import get_clan_data
# Não precisamos mais importar a função de top 5 aqui por enquanto
# from utils.database import get_top_war_performers

st.set_page_config(page_title="Info do Clã", page_icon="ℹ️", layout="wide")

if 'clan_tag' not in st.session_state or not st.session_state['clan_tag']:
    st.warning("🔒 Por favor, faça o login na página principal para visualizar as informações do clã.")
    st.page_link("app.py", label="Ir para a página de Login", icon="🔑")
else:
    try:
        clan_tag = st.session_state['clan_tag']
        coc_email = st.secrets.get("coc_email")
        coc_password = st.secrets.get("coc_password")

        df_members, clan_name, clan_badge_url = get_clan_data(clan_tag, coc_email, coc_password)
        
        if df_members is not None and not df_members.empty:
            
            col_title1, col_title2 = st.columns([1, 10])
            with col_title1:
                st.image(clan_badge_url, width=100)
            with col_title2:
                st.title(f"Dashboard do Clã: {clan_name}")
            
            st.divider()

            st.header("Métricas Principais do Clã")
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("👥 Total de Membros", f"{len(df_members)} / 50")
            if 'Troféus' in df_members.columns:
                kpi2.metric("🏆 Média de Troféus", f"{int(df_members['Troféus'].mean()):,}".replace(",", "."))
            if 'CV' in df_members.columns:
                kpi3.metric("🏰 CV Médio", f"{df_members['CV'].mean():.2f}")

            st.divider()
            
            # --- LAYOUT ATUALIZADO ---
            col_chart, col_top5 = st.columns(2)
            with col_chart:
                st.header("📊 Composição do Clã")
                if 'CV' in df_members.columns:
                    df_cv_counts = df_members['CV'].value_counts().sort_index()
                    st.bar_chart(df_cv_counts)
            
            with col_top5:
                st.header("⭐ Destaques de Guerras")
                st.subheader("🏆 Top 5 - Últimas 5 Guerras")
                # Mensagem de placeholder
                st.info("Em construção...")

            st.divider()

            # (O resto da página com a tabela principal continua igual)
            st.header("Membros Atuais")
            # ... (seu código da tabela st.dataframe) ...

        else:
            st.error("Não foi possível carregar os dados do clã.")
            
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")

