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
            return {'Nome': player.name, 'Cargo': player.role.name, 'CV': player.town_hall, 'Liga': player.league.name if player.league else 'Sem Liga', 'Troféus': player.trophies, 'Rei Bárbaro': hero_levels.get('Barbarian King', 0), 'Rainha Arqueira': hero_levels.get('Archer Queen', 0), 'Grande Guardião': hero_levels.get('Grand Warden', 0), 'Campeã Real': hero_levels.get('Royal Champion', 0)}
        tasks = [fetch_player_data(member) for member in clan.members]
        members_data = await asyncio.gather(*tasks)
        return pd.DataFrame(members_data), clan.name
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
        if not existing_client:
            await client.close()

async def _generate_full_league_preview_async(our_clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        our_war_summary, df_our_clan, _, _, _ = await _get_cwl_current_war_details_async(our_clan_tag, coc_email, coc_password, existing_client=client)
        if our_war_summary is None:
            return None, None, "Não foi possível carregar nossa guerra atual."
        
        all_clans = await _get_cwl_group_clans_async(our_clan_tag, coc_email, coc_password, existing_client=client)
        if not all_clans:
            return None, None, "Não foi possível carregar a lista de clãs do grupo."
            
        opponents = [clan for clan in all_clans if clan.tag != our_clan_tag]
        tasks = [_get_cwl_current_war_details_async(opponent.tag, coc_email, coc_password, existing_client=client) for opponent in opponents]
        scouting_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        league_preview = []
        for i, result in enumerate(scouting_results):
            opponent_name = opponents[i].name
            if isinstance(result, Exception) or result[0] is None:
                df_predicted_opponent = pd.DataFrame([{"Erro": f"Não foi possível carregar a guerra de {opponent_name}."}])
            else:
                _, their_clan_df, their_opponent_df, their_clan_tag, _ = result
                df_predicted_opponent = their_clan_df if their_clan_tag == opponents[i].tag else their_opponent_df
            league_preview.append({'opponent_name': opponent_name, 'predicted_lineup': df_predicted_opponent})
            
        return df_our_clan, league_preview
    finally:
        await client.close()


