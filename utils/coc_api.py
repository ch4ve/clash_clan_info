import streamlit as st
import pandas as pd
import coc
import asyncio
from collections import defaultdict

# --- FUNÇÕES SÍNCRONAS (WRAPPERS) ---
# O Streamlit chama estas funções. Elas usam asyncio.run() para executar a lógica assíncrona.

@st.cache_data(ttl="10m")
def get_clan_data(clan_tag, coc_email, coc_password):
    return asyncio.run(_get_clan_data_async(clan_tag, coc_email, coc_password))

@st.cache_data(ttl="5m")
def get_current_war_data(clan_tag, coc_email, coc_password):
    return asyncio.run(_get_current_war_data_async(clan_tag, coc_email, coc_password))

@st.cache_data(ttl="2h")
def get_cwl_data(clan_tag, coc_email, coc_password):
    return asyncio.run(_get_cwl_data_async(clan_tag, coc_email, coc_password))

@st.cache_data(ttl="5m")
def get_cwl_current_war_details(clan_tag, coc_email, coc_password):
    return asyncio.run(_get_cwl_current_war_details_async(clan_tag, coc_email, coc_password))

@st.cache_data(ttl="12h")
def get_cwl_group_clans(clan_tag, coc_email, coc_password):
    return asyncio.run(_get_cwl_group_clans_async(clan_tag, coc_email, coc_password))

@st.cache_data(ttl="5m")
def generate_full_league_preview(our_clan_tag, coc_email, coc_password):
    return asyncio.run(_generate_full_league_preview_async(our_clan_tag, coc_email, coc_password))


# --- LÓGICA ASSÍNCRONA (CORE) ---
# As funções com "_" na frente contêm a lógica real que conversa com a API.

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

async def _get_current_war_data_async(clan_tag, coc_email, coc_password):
    # (Lógica da função que já tínhamos)
    pass

async def _get_cwl_data_async(clan_tag, coc_email, coc_password):
    # (Lógica da função que já tínhamos)
    pass

async def _get_cwl_current_war_details_async(clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
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

async def _get_cwl_group_clans_async(clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        group = await client.get_league_group(clan_tag)
        return group.clans
    finally:
        await client.close()

async def _generate_full_league_preview_async(our_clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        
        # Tarefas para buscar nossa guerra e a lista de clãs em paralelo
        our_war_task = asyncio.create_task(_get_cwl_current_war_details_async_internal(our_clan_tag, client))
        clans_list_task = asyncio.create_task(_get_cwl_group_clans_async_internal(our_clan_tag, client))

        our_war_summary, df_our_clan, _, _, _ = await our_war_task
        all_clans = await clans_list_task

        if df_our_clan is None or all_clans is None:
            return None, None

        opponents = [clan for clan in all_clans if clan.tag != our_clan_tag]
        
        # Tarefas para espionar cada oponente em paralelo
        scouting_tasks = [_get_cwl_current_war_details_async_internal(opponent.tag, client) for opponent in opponents]
        scouting_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        league_preview = []
        for i, result in enumerate(scouting_results):
            opponent_name = opponents[i].name
            if isinstance(result, Exception) or result[0] is None:
                df_predicted_opponent = pd.DataFrame([{"Erro": "Não foi possível carregar a guerra deste clã."}])
            else:
                _, their_clan_df, their_opponent_df, their_clan_tag, _ = result
                df_predicted_opponent = their_clan_df if their_clan_tag == opponents[i].tag else their_opponent_df
            
            league_preview.append({'opponent_name': opponent_name, 'predicted_lineup': df_predicted_opponent})
            
        return df_our_clan, league_preview
    finally:
        await client.close()

# Funções "internas" para serem usadas pela espionagem em massa, reutilizando o cliente
async def _get_cwl_current_war_details_async_internal(clan_tag, client):
    group = await client.get_league_group(clan_tag)
    async for war in group.get_wars_for_clan(clan_tag):
        if war.state in ['preparation', 'inWar']:
            clan_side = war.clan if war.clan.tag == clan_tag else war.opponent
            opponent_side = war.opponent if war.clan.tag == clan_tag else war.clan
            # ... (resto da lógica igual à função principal)
            return war_summary, df_clan, df_opponent, clan_side.tag, opponent_side.tag
    return None, None, None, None, None

async def _get_cwl_group_clans_async_internal(clan_tag, client):
    group = await client.get_league_group(clan_tag)
    return group.clans
