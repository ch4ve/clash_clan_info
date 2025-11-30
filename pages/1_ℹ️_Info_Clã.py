import streamlit as st
import pandas as pd
from utils.coc_api import get_clan_data

st.set_page_config(page_title="Info do Clã", page_icon="ℹ️", layout="wide")

if 'clan_tag' not in st.session_state or not st.session_state['clan_tag']:
    st.warning("🔒 Por favor, faça o login na página principal para visualizar as informações do clã.")
    st.page_link("app.py", label="Ir para a página de Login", icon="🔑")
else:
    try:
        clan_tag = st.session_state['clan_tag']
        coc_email = st.secrets.get("coc_email")
        coc_password = st.secrets.get("coc_password")

        with st.spinner("Buscando e analisando dados do clã..."):
            # Busca os dados (sem precisar alterar a função na API)
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

            # --- BLOCO DOS KPIs (MÉTRICAS) ---
            st.header("Métricas Principais do Clã")
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("👥 Total de Membros", f"{len(df_members)} / 50")
            if 'Troféus' in df_members.columns:
                kpi2.metric("🏆 Média de Troféus", f"{int(df_members['Troféus'].mean()):,}".replace(",", "."))
            if 'CV' in df_members.columns:
                kpi3.metric("🏰 CV Médio", f"{df_members['CV'].mean():.2f}")

            st.divider()
            
            # --- BLOCOS DO GRÁFICO E DESTAQUES ---
            col_chart, col_top5 = st.columns(2)
            with col_chart:
                st.header("📊 Composição do Clã")
                if 'CV' in df_members.columns:
                    df_cv_counts = df_members['CV'].value_counts().sort_index()
                    st.bar_chart(df_cv_counts)
            
            with col_top5:
                st.header("⭐ Destaques de Guerras")
                st.subheader("🏆 Top 5 - Últimas 5 Guerras")
                st.info("Em construção...")

            st.divider()

            # --- TABELA DE SELEÇÃO PARA A LIGA ---
            st.header("Planejamento de Escalação (CWL)")
            st.caption("Selecione os membros na tabela abaixo para gerar a lista da liga.")

            # Prepara os dados para a tabela
            if 'Tag' in df_members.columns:
                df_members['Link'] = df_members['Tag'].apply(lambda tag: f"https://www.clashofstats.com/players/{tag.strip('#')}/summary")
            
            # Adiciona a coluna de seleção (checkbox) iniciada como Falso
            if "Selecionar" not in df_members.columns:
                df_members.insert(0, "Selecionar", False)

            # Usamos data_editor para permitir interação
            edited_df = st.data_editor(
                df_members,
                column_config={
                    "Selecionar": st.column_config.CheckboxColumn(
                        "Selecionar",
                        help="Marque para incluir este jogador na lista da liga",
                        default=False,
                    ),
                    "Ícone Liga": st.column_config.ImageColumn("Liga"),
                    "Link": st.column_config.LinkColumn("Perfil Externo", display_text="Abrir ↗️"),
                    "Tag": None # Esconde a tag
                },
                column_order=["Selecionar", "Nome", "Cargo", "CV", "Ícone Liga", "Troféus", "Link"],
                hide_index=True,
                use_container_width=True,
                disabled=["Nome", "Cargo", "CV", "Ícone Liga", "Troféus", "Link"] # Impede edição das outras colunas
            )

            st.divider()

            # --- BOTÃO E LISTA DE SELECIONADOS ---
            if st.button("Gerar Lista de Selecionados para Liga"):
                # Filtra apenas quem foi marcado com 'True'
                selecionados = edited_df[edited_df["Selecionar"] == True]
                
                if not selecionados.empty:
                    # Ordena por CV (do maior para o menor) para facilitar a organização
                    lista_final = selecionados[['Nome', 'CV']].sort_values(by='CV', ascending=False)
                    
                    st.success(f"Lista gerada com {len(lista_final)} jogadores!")
                    
                    # Mostra a tabela limpa
                    st.dataframe(lista_final, hide_index=True, use_container_width=True)
                else:
                    st.warning("Nenhum jogador foi selecionado na tabela acima.")

        else:
            st.error("Não foi possível carregar os dados do clã.")
            
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")
