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

        # --- LÓGICA DE CACHE MANUAL ---
        # Verifica se os dados JÁ estão salvos na memória para este clã específico.
        # Se não estiverem (ou se o clã mudou), buscamos na API.
        if 'clan_data_cache' not in st.session_state or st.session_state.get('cached_clan_tag') != clan_tag:
            with st.spinner("Buscando e analisando dados do clã (Isso acontece apenas uma vez)..."):
                df_members, clan_name, clan_badge_url = get_clan_data(clan_tag, coc_email, coc_password)
                
                if df_members is not None and not df_members.empty:
                    # Adiciona a coluna de seleção ao DataFrame antes de salvar
                    if "Selecionar" not in df_members.columns:
                        df_members.insert(0, "Selecionar", False)
                    
                    # Cria os links
                    if 'Tag' in df_members.columns:
                        df_members['Link'] = df_members['Tag'].apply(lambda tag: f"https://www.clashofstats.com/players/{tag.strip('#')}/summary")

                    # Salva tudo no session_state
                    st.session_state['clan_data_cache'] = {
                        'df': df_members,
                        'name': clan_name,
                        'badge': clan_badge_url
                    }
                    st.session_state['cached_clan_tag'] = clan_tag
                else:
                    st.error("Não foi possível carregar os dados do clã.")
                    st.stop() # Para a execução se falhar

        # --- RECUPERA OS DADOS DA MEMÓRIA ---
        # A partir daqui, usamos APENAS os dados que estão no cache, sem chamar a API.
        cache = st.session_state['clan_data_cache']
        df_members = cache['df']
        clan_name = cache['name']
        clan_badge_url = cache['badge']
        
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

        # Usamos data_editor para permitir interação
        # O data_editor retorna um NOVO dataframe com as edições, mas não altera o original no cache automaticamente
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
            disabled=["Nome", "Cargo", "CV", "Ícone Liga", "Troféus", "Link"], # Impede edição das outras colunas
            key="editor_membros" # Chave única para ajudar o Streamlit a gerenciar o estado
        )

        st.divider()

        # --- CONTADOR DE SELECIONADOS ---
        # Calcula quantos estão selecionados no momento
        num_selecionados = edited_df["Selecionar"].sum()

        # --- BOTÃO E LISTA DE SELECIONADOS ---
        col_btn, col_info = st.columns([1, 2])
        
        with col_btn:
            if st.button("Gerar Lista de Selecionados para Liga"):
                # Filtra apenas quem foi marcado com 'True'
                selecionados = edited_df[edited_df["Selecionar"] == True]
                
                if not selecionados.empty:
                    # Ordena por CV (do maior para o menor) para facilitar a organização
                    lista_final = selecionados.sort_values(by='CV', ascending=False)
                    
                    st.success(f"Lista gerada com {len(lista_final)} jogadores!")
                    
                    # Gera o texto formatado para copiar
                    texto_copia = ""
                    for index, row in lista_final.iterrows():
                        texto_copia += f"{row['Nome']} (CV {row['CV']})\n"
                    
                    # Mostra como um bloco de código fácil de copiar
                    st.text_area("Copie a lista abaixo:", value=texto_copia, height=300)
                else:
                    st.warning("Nenhum jogador foi selecionado na tabela acima.")
        
        with col_info:
            # Mostra o contador dinâmico ao lado do botão
            st.info(f"**Jogadores Selecionados:** {num_selecionados}")
            
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")
