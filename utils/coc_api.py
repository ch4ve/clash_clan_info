# Este é o novo conteúdo de utils/coc_api.py

import streamlit as st
import pandas as pd
import coc
import asyncio

# --- FUNÇÃO PARA DADOS GERAIS DO CLÃ ---
@st.cache_data(ttl="10m")
def get_clan_data(clan_tag, coc_email, coc_password):
    # (Esta função continua a mesma de antes)
    async def _fetch():
        client = coc.Client()
        try:
            await client.login(coc_email, coc_password)
            clan = await client.get_clan(clan_tag)
            members_data = []
            for member in clan.members:
                player = await client.get_player(member.tag)
                hero_levels = {h.name: h.level for h in player.heroes}
                members_data.append({
                    'Nome': player.name, 'Cargo': player.role, 'CV': player.town_hall,
                    'Liga': player.league.name if player.league else 'Sem Liga', 'Troféus': player.trophies,
                    'Rei Bárbaro': hero_levels.get('Barbarian King', 0), 'Rainha Arqueira': hero_levels.get('Archer Queen', 0),
                    'Grande Guardião': hero_levels.get('Grand Warden', 0), 'Campeã Real': hero_levels.get('Royal Champion', 0)
                })
            return pd.DataFrame(members_data), clan.name
        except Exception as e:
            raise e
        finally:
            await client.close()
    return asyncio.run(_fetch())

# --- FUNÇÃO PARA DADOS DA GUERRA ATUAL ---
# Em utils/coc_api.py

@st.cache_data(ttl="5m")
def get_current_war_data(clan_tag, coc_email, coc_password):
    """
    Função assíncrona para buscar dados detalhados da guerra atual,
    incluindo totais de destruição e duração dos ataques.
    """
    async def _fetch_war():
        client = coc.Client()
        try:
            await client.login(coc_email, coc_password)
            
            try:
                war = await client.get_current_war(clan_tag)
            except coc.NotFound:
                return None, None, None, None 

            opponent_map = {opponent.tag: opponent for opponent in war.opponent.members}
            attacks_data = []

            for member in war.clan.members:
                ataques_feitos = len(member.attacks)
                estrelas_atk1, cv_inimigo_atk1, destruicao_atk1, duracao_atk1 = 0, "-", 0, 0
                estrelas_atk2, cv_inimigo_atk2, destruicao_atk2, duracao_atk2 = 0, "-", 0, 0

                if ataques_feitos >= 1:
                    atk1 = member.attacks[0]
                    estrelas_atk1, destruicao_atk1, duracao_atk1 = atk1.stars, atk1.destruction, atk1.duration
                    inimigo1 = opponent_map.get(atk1.defender_tag)
                    if inimigo1: cv_inimigo_atk1 = inimigo1.town_hall
                
                if ataques_feitos == 2:
                    atk2 = member.attacks[1]
                    estrelas_atk2, destruicao_atk2, duracao_atk2 = atk2.stars, atk2.destruction, atk2.duration
                    inimigo2 = opponent_map.get(atk2.defender_tag)
                    if inimigo2: cv_inimigo_atk2 = inimigo2.town_hall

                attacks_data.append({
                    'Posição': member.map_position, 'Nome': member.name, 'Ataques Feitos': ataques_feitos,
                    'Estrelas Atk 1': estrelas_atk1, 'CV Inimigo Atk 1': cv_inimigo_atk1,
                    'Estrelas Atk 2': estrelas_atk2, 'CV Inimigo Atk 2': cv_inimigo_atk2,
                    'Destruição Atk 1': destruicao_atk1, 'Duração Atk 1 (s)': duracao_atk1,
                    'Destruição Atk 2': destruicao_atk2, 'Duração Atk 2 (s)': duracao_atk2
                })
            
            df_attacks = pd.DataFrame(attacks_data)
            
            # --- CÁLCULOS DAS COLUNAS DE TOTAIS ---
            df_attacks['Estrelas Totais'] = df_attacks['Estrelas Atk 1'] + df_attacks['Estrelas Atk 2']
            df_attacks['Destruição Total'] = df_attacks['Destruição Atk 1'] + df_attacks['Destruição Atk 2']
            df_attacks['Duração Total (s)'] = df_attacks['Duração Atk 1 (s)'] + df_attacks['Duração Atk 2 (s)'] # <-- NOVO CÁLCULO
            
            # --- FORMATAÇÃO PARA EXIBIÇÃO ---
            df_attacks['Destruição Total'] = df_attacks['Destruição Total'].apply(lambda x: f"{x}%")
            
            # Esconde colunas individuais para a tabela final ficar mais limpa
            colunas_para_remover = ['Destruição Atk 1', 'Duração Atk 1 (s)', 'Destruição Atk 2', 'Duração Atk 2 (s)']
            df_display = df_attacks.drop(columns=colunas_para_remover)
            
            # Reorganiza as colunas para a nova ordem desejada
            ordem_colunas_display = [
                'Posição', 'Nome', 'Ataques Feitos', 'Estrelas Totais', 'Estrelas Atk 1', 
                'CV Inimigo Atk 1', 'Estrelas Atk 2', 'CV Inimigo Atk 2',
                'Destruição Total', 'Duração Total (s)' # <-- NOVA COLUNA NO FINAL
            ]
            df_display = df_display[ordem_colunas_display]
            
            df_display = df_display.sort_values(by='Posição', ascending=True)
            
            war_summary = {
                "clan_name": war.clan.name, "opponent_name": war.opponent.name,
                "clan_stars": war.clan.stars, "opponent_stars": war.opponent.stars,
                "clan_destruction": war.clan.destruction, "opponent_destruction": war.opponent.destruction
            }
            # IMPORTANTE: Retornamos o DataFrame COMPLETO (df_attacks) para salvar no DB, 
            # mas exibiremos o DataFrame LIMPO (df_display). Vamos ajustar a página para isso.
            return df_attacks, df_display, war_summary, war.state, war.end_time

        except Exception as e:
            raise e
        finally:
            await client.close()
            
    return asyncio.run(_fetch_war())

# --- NOVA FUNÇÃO PARA DADOS DA LIGA DE CLÃS (CWL) ---
@st.cache_data(ttl="2h")
def get_cwl_data(clan_tag, coc_email, coc_password):
    """
    Busca e consolida todos os dados de ataque da CWL atual,
    usando o método correto para a v3.9.1 da biblioteca.
    """
    async def _fetch_cwl():
        client = coc.Client()
        try:
            await client.login(coc_email, coc_password)
            
            try:
                # 1. Usando a função correta: get_league_group()
                group = await client.get_league_group(clan_tag)
            except coc.NotFound:
                return None, None 

            all_attacks_data = []
            
            # 2. Usando o método mais simples para iterar sobre as guerras do clã
            war_day = 0
            async for war in group.get_wars_for_clan(clan_tag):
                war_day += 1
                # Garante que 'clan_side' seja o nosso clã
                clan_side = war.clan if war.clan.tag == clan_tag else war.opponent

                for member in clan_side.members:
                    if member.attacks:
                        attack = member.attacks[0]
                        all_attacks_data.append({
                            'Tag do Jogador': member.tag,
                            'Nome': member.name,
                            'Dia da Guerra': war_day,
                            'Estrelas': attack.stars
                        })
            
            if not all_attacks_data:
                return pd.DataFrame(), group.season

            # O resto da lógica de processamento com Pandas continua a mesma
            df_attacks = pd.DataFrame(all_attacks_data)
            summary = df_attacks.groupby(['Tag do Jogador', 'Nome']).agg(
                Total_Estrelas=('Estrelas', 'sum'),
                Ataques_Feitos=('Estrelas', 'size')
            ).reset_index()

            summary['Media_Estrelas'] = (summary['Total_Estrelas'] / summary['Ataques_Feitos']).round(2)
            total_guerras_registradas = df_attacks['Dia da Guerra'].nunique()
            summary['Guerras_Ausente'] = total_guerras_registradas - summary['Ataques_Feitos']
            
            summary = summary.sort_values(by='Total_Estrelas', ascending=False)
            
            summary.rename(columns={
                'Nome': 'Nome do Jogador', 'Total_Estrelas': 'Total de Estrelas',
                'Ataques_Feitos': 'Ataques Feitos', 'Media_Estrelas': 'Média de Estrelas',
                'Guerras_Ausente': 'Guerras Ausente'
            }, inplace=True)

            return summary, group.season

        except Exception as e:
            raise e
        finally:
            await client.close()
            
    return asyncio.run(_fetch_cwl())



