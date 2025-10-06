# Conteúdo COMPLETO e FINAL de pages/1_ℹ️_Info_Clã.py

import streamlit as st
import pandas as pd
# Importações corretas, apontando para sua estrutura 'utils'
from utils.coc_api import get_clan_data 
from utils.database import get_top_war_performers

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
            
            # --- TÍTULO COM EMBLEMA DO CLÃ ---
            col_title1, col_title2 = st.columns([1, 10])
            with col_title1:
                st.image(clan_badge_url, width=100)
            with col_title2:
                st.title(f"Dashboard do Clã: {clan_name}")
                st.success(f"Exibindo dados para o clã: {clan_tag}")
            
            st.divider()

            # --- BLOCO DOS KPIs (MÉTRICAS) RESTAURADO ---
            st.header("Métricas Principais do Clã")
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("👥 Total de Membros", f"{len(df_members)} / 50")
            # Adicionada verificação para evitar erro se a coluna não existir
            if 'Troféus' in df_members.columns:
                kpi2.metric("🏆 Média de Troféus", f"{int(df_members['Troféus'].mean()):,}".replace(",", "."))
            if 'CV' in df_members.columns:
                kpi3.metric("🏰 CV Médio", f"{df_members['CV'].mean():.2f}")

            st.divider()
            
            # --- BLOCOS DO GRÁFICO E TOP 5 RESTAURADOS ---
            col_chart, col_top5 = st.columns(2)
            with col_chart:
                st.header("📊 Composição do Clã")
                if 'CV' in df_members.columns:
                    df_cv_counts = df_members['CV'].value_counts().sort_index()
                    st.bar_chart(df_cv_counts)
            
            with col_top5:
                st.header("⭐ Destaques de Guerras")
                # Verificação se a função get_top_war_performers existe no database.py
                try:
                    from utils.database import get_top_war_performers
                    st.subheader("🏆 Top 5 - Últimas 5 Guerras")
                    df_top5_wars = get_top_war_performers()
                    if not df_top5_wars.empty:
                        df_top5_wars_with_cv = pd.merge(df_top5_wars, df_members[['Nome', 'CV']], on='Nome', how='left').fillna(0)
                        df_top5_wars_with_cv['Total Destruição'] = df_top5_wars_with_cv['Total Destruição'].apply(lambda x: f"{x}%")
                        st.dataframe(df_top5_wars_with_cv[['Nome', 'CV', 'Total Estrelas', 'Total Destruição']], hide_index=True)
                    else:
                        st.info("Não há dados de guerras suficientes no histórico.")
                except ImportError:
                    st.info("A função de ranking Top 5 está em desenvolvimento.")

            st.divider()

            # --- TABELA COMPLETA DE MEMBROS COM LINKS ---
            st.header("Membros Atuais")
            df_members['Link'] = df_members['Tag'].apply(lambda tag: f"https://www.clashofstats.com/players/{tag.strip('#')}/summary")
            st.dataframe(
                df_members,
                column_config={
                    "Ícone Liga": st.column_config.ImageColumn("Liga"),
                    "Link": st.column_config.LinkColumn("Perfil Externo", display_text="Abrir ↗️"),
                    "Tag": None
                },
                column_order=["Nome", "Cargo", "CV", "Ícone Liga", "Troféus", "Link"],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.error("Não foi possível carregar os dados do clã.")
            
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")
