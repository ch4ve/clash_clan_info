import pandas as pd
import coc
import asyncio
from collections import defaultdict
from .loop_manager import loop_manager  # Usando importação relativa

# --- FUNÇÕES SÍNCRONAS (WRAPPERS) ---
# O Streamlit chama estas funções. Elas repassam o trabalho para o gerente.
def get_clan_data(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(_get_clan_data_async(clan_tag, coc_email, coc_password))
def get_cwl_data(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(_get_cwl_data_async(clan_tag, coc_email, coc_password))
def get_cwl_current_war_details(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(_get_cwl_current_war_details_async(clan_tag, coc_email, coc_password))
def get_cwl_group_clans(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(_get_cwl_group_clans_async(clan_tag, coc_email, coc_password))
def generate_full_league_preview(our_clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(_generate_full_league_preview_async(our_clan_tag, coc_email, coc_password))
def get_current_war_data(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(_get_current_war_data_async(clan_tag, coc_email, coc_password))
# --- LÓGICA ASSÍNCRONA (CORE) ---
async def _get_clan_data_async(clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        clan = await client.get_clan(clan_tag)
        
        async def fetch_player_data(member):
            player = await client.get_player(member.tag)
            hero_levels = {h.name: h.level for h in player.heroes}
            return {
                'Tag': player.tag, # <-- INFORMAÇÃO DA TAG ADICIONADA
                'Nome': player.name,
                'Cargo': player.role.name,
                'CV': player.town_hall,
                'Liga': player.league.name if player.league else 'Sem Liga',
                'Ícone Liga': player.league.icon.url if player.league else None,
                'Troféus': player.trophies,
                'Rei Bárbaro': hero_levels.get('Barbarian King', 0),
                'Rainha Arqueira': hero_levels.get('Archer Queen', 0),
                'Grande Guardião': hero_levels.get('Grand Warden', 0),
                'Campeã Real': hero_levels.get('Royal Champion', 0)
            }

        tasks = [fetch_player_data(member) for member in clan.members]
        members_data = await asyncio.gather(*tasks)
        
        return pd.DataFrame(members_data), clan.name, clan.badge.url
    finally:
        await client.close()

async def _get_cwl_data_async(clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        group = await client.get_league_group(clan_tag)
        all_attacks_data = []
        war_day = 0
        async for war in group.get_wars_for_clan(clan_tag):
            war_day += 1
            clan_side = war.clan if war.clan.tag == clan_tag else war.opponent
            for member in clan_side.members:
                if member.attacks:
                    attack = member.attacks[0]
                    all_attacks_data.append({'Tag do Jogador': member.tag, 'Nome': member.name, 'Dia da Guerra': war_day, 'Estrelas': attack.stars})
        if not all_attacks_data:
            return pd.DataFrame(), group.season
        df_attacks = pd.DataFrame(all_attacks_data)
        summary = df_attacks.groupby(['Tag do Jogador', 'Nome']).agg(Total_Estrelas=('Estrelas', 'sum'), Ataques_Feitos=('Estrelas', 'size')).reset_index()
        summary['Media_Estrelas'] = (summary['Total_Estrelas'] / summary['Ataques_Feitos']).round(2)
        total_guerras = df_attacks['Dia da Guerra'].nunique()
        summary['Guerras_Ausente'] = total_guerras - summary['Ataques_Feitos']
        summary = summary.sort_values(by='Total_Estrelas', ascending=False)
        summary.rename(columns={'Nome': 'Nome do Jogador', 'Total_Estrelas': 'Total de Estrelas','Ataques_Feitos': 'Ataques Feitos', 'Media_Estrelas': 'Média de Estrelas','Guerras_Ausente': 'Guerras Ausente'}, inplace=True)
        return summary, group.season
    finally:
        await client.close()

async def _get_cwl_group_clans_async(clan_tag, coc_email, coc_password, existing_client=None):
    client = existing_client or coc.Client()
    try:
        if not existing_client:
            await client.login(coc_email, coc_password)
        group = await client.get_league_group(clan_tag)
        return group.clans
    finally:
        if not existing_client:
            await client.close()

async def _get_cwl_current_war_details_async(clan_tag, coc_email, coc_password, existing_client=None):
    client = existing_client or coc.Client()
    try:
        if not existing_client:
            await client.login(coc_email, coc_password)
        group = await client.get_league_group(clan_tag)
        async for war in group.get_wars_for_clan(clan_tag):
            if war.state in ['preparation', 'inWar']:
                clan_side = war.clan if war.clan.tag == clan_tag else war.opponent
                opponent_side = war.opponent if war.clan.tag == clan_tag else war.clan
                clan_members_data = [{'Pos.': m.map_position, 'Nome': m.name, 'CV': m.town_hall} for m in clan_side.members]
                df_clan = pd.DataFrame(clan_members_data).sort_values(by='Pos.')
                opponent_members_data = [{'Pos.': m.map_position, 'Nome': m.name, 'CV': m.town_hall} for m in opponent_side.members]
                df_opponent = pd.DataFrame(opponent_members_data).sort_values(by='Pos.')
                war_summary = {"clan_name": clan_side.name, "opponent_name": opponent_side.name, "state": war.state, "start_time": war.start_time, "end_time": war.end_time}
                return war_summary, df_clan, df_opponent, clan_side.tag, opponent_side.tag
        return None, None, None, None, None
    finally:
        await client.close()

async def _generate_full_league_preview_async(our_clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        
        # Helper interno para reutilizar lógica
        async def _internal_get_war_details(tag, shared_client):
            group = await shared_client.get_league_group(tag)
            async for war in group.get_wars_for_clan(tag):
                if war.state in ['preparation', 'inWar']:
                    clan_side = war.clan if war.clan.tag == tag else war.opponent
                    opponent_side = war.opponent if war.clan.tag == tag else war.clan
                    clan_members_data = [{'Pos.': m.map_position, 'Nome': m.name, 'CV': m.town_hall} for m in clan_side.members]
                    df_clan = pd.DataFrame(clan_members_data).sort_values(by='Pos.')
                    opponent_members_data = [{'Pos.': m.map_position, 'Nome': m.name, 'CV': m.town_hall} for m in opponent_side.members]
                    df_opponent = pd.DataFrame(opponent_members_data).sort_values(by='Pos.')
                    war_summary = {"clan_name": clan_side.name, "opponent_name": opponent_side.name}
                    return war_summary, df_clan, df_opponent, clan_side.tag
            return None, None, None, None

        our_war_summary, df_our_clan, _, _ = await _internal_get_war_details(our_clan_tag, client)
        if our_war_summary is None:
            return None, None, "Não foi possível carregar nossa guerra atual."
        
        all_clans = await _get_cwl_group_clans_async(our_clan_tag, coc_email, coc_password, existing_client=client)
        if not all_clans:
            return None, None, "Não foi possível carregar a lista de clãs do grupo."
            
        opponents = [clan for clan in all_clans if clan.tag != our_clan_tag]
        
        tasks = [_internal_get_war_details(opponent.tag, client) for opponent in opponents]
        scouting_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        league_preview = []
        for i, result in enumerate(scouting_results):
            opponent_name = opponents[i].name
            if isinstance(result, Exception) or result is None:
                df_predicted_opponent = pd.DataFrame([{"Erro": f"Não foi possível carregar a guerra de {opponent_name}."}])
            else:
                _, their_clan_df, their_opponent_df, their_clan_tag = result
                df_predicted_opponent = their_clan_df if their_clan_tag == opponents[i].tag else their_opponent_df
            
            league_preview.append({'opponent_name': opponent_name, 'predicted_lineup': df_predicted_opponent})
            
        # --- A CORREÇÃO ESTÁ AQUI ---
        # A função agora retorna os 3 valores que a página espera
        return df_our_clan, league_preview, our_war_summary.get('clan_name', 'Nosso Clã')
    finally:
        await client.close()

async def _get_current_war_data_async(clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        war = await client.get_current_war(clan_tag)
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
            attacks_data.append({'Posição': member.map_position, 'Nome': member.name, 'Ataques Feitos': ataques_feitos, 'Estrelas Atk 1': estrelas_atk1, 'CV Inimigo Atk 1': cv_inimigo_atk1, 'Estrelas Atk 2': estrelas_atk2, 'CV Inimigo Atk 2': cv_inimigo_atk2, 'Destruição Atk 1': destruicao_atk1, 'Duração Atk 1 (s)': duracao_atk1, 'Destruição Atk 2': destruicao_atk2, 'Duração Atk 2 (s)': duracao_atk2})
        df_attacks = pd.DataFrame(attacks_data)
        if not df_attacks.empty:
            df_attacks['Estrelas Totais'] = df_attacks['Estrelas Atk 1'] + df_attacks['Estrelas Atk 2']
            df_attacks['Destruição Total'] = df_attacks['Destruição Atk 1'] + df_attacks['Destruição Atk 2']
            df_attacks['Duração Total (s)'] = df_attacks['Duração Atk 1 (s)'] + df_attacks['Duração Atk 2 (s)']
            df_display = df_attacks.copy()
            df_display['Destruição Total'] = df_display['Destruição Total'].apply(lambda x: f"{x}%")
            df_display = df_display.drop(columns=['Destruição Atk 1', 'Duração Atk 1 (s)', 'Destruição Atk 2', 'Duração Atk 2 (s)'])
            ordem_colunas_display = ['Posição', 'Nome', 'Ataques Feitos', 'Estrelas Totais', 'Estrelas Atk 1', 'CV Inimigo Atk 1', 'Estrelas Atk 2', 'CV Inimigo Atk 2', 'Destruição Total', 'Duração Total (s)']
            df_display = df_display[ordem_colunas_display].sort_values(by='Posição', ascending=True)
        else:
            df_display = pd.DataFrame()
        war_summary = {"clan_name": war.clan.name, "opponent_name": war.opponent.name, "clan_stars": war.clan.stars, "opponent_stars": war.opponent.stars, "clan_destruction": war.clan.destruction, "opponent_destruction": war.opponent.destruction}
        return df_attacks, df_display, war_summary, war.state, war.end_time
    except coc.NotFound:
        return None, None, None, None, None
    finally:
        await client.close()









