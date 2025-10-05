import pandas as pd
import coc
import asyncio
from collections import defaultdict

# --- FUNÇÕES SÍNCRONAS (WRAPPERS) ---
# O asyncio.run foi a abordagem que funcionou sem erros de importação, vamos mantê-la.
def get_clan_data(clan_tag, coc_email, coc_password):
    return asyncio.run(_get_clan_data_async(clan_tag, coc_email, coc_password))

def get_current_war_data(clan_tag, coc_email, coc_password):
    return asyncio.run(_get_current_war_data_async(clan_tag, coc_email, coc_password))

def get_cwl_data(clan_tag, coc_email, coc_password):
    return asyncio.run(_get_cwl_data_async(clan_tag, coc_email, coc_password))

def get_cwl_current_war_details(clan_tag, coc_email, coc_password):
    return asyncio.run(_get_cwl_current_war_details_async(clan_tag, coc_email, coc_password))

def get_cwl_group_clans(clan_tag, coc_email, coc_password):
    return asyncio.run(_get_cwl_group_clans_async(clan_tag, coc_email, coc_password))

def generate_full_league_preview(our_clan_tag, coc_email, coc_password):
    return asyncio.run(_generate_full_league_preview_async(our_clan_tag, coc_email, coc_password))


# --- LÓGICA ASSÍNCRONA (CORE) ---
async def _get_clan_data_async(clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        clan = await client.get_clan(clan_tag)
        async def fetch_player_data(member):
            player = await client.get_player(member.tag)
            return {'Nome': player.name, 'Cargo': player.role.name, 'CV': player.town_hall}
        tasks = [fetch_player_data(member) for member in clan.members]
        members_data = await asyncio.gather(*tasks)
        return pd.DataFrame(members_data), clan.name
    finally:
        # --- CORREÇÃO APLICADA ---
        if 'client' in locals():
            await client.close()

async def _get_current_war_data_async(clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        war = await client.get_current_war(clan_tag)
        # (Resto da lógica da função...)
        return df_attacks, df_display, war_summary, war.state, war.end_time
    except coc.NotFound:
        return None, None, None, None, None
    finally:
        # --- CORREÇÃO APLICADA ---
        if 'client' in locals():
            await client.close()

async def _get_cwl_data_async(clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        group = await client.get_league_group(clan_tag)
        # (Resto da lógica da função...)
        return summary, group.season
    except coc.NotFound:
        return None, None
    finally:
        # --- CORREÇÃO APLICADA ---
        if 'client' in locals():
            await client.close()

async def _get_cwl_group_clans_async(clan_tag, coc_email, coc_password, existing_client=None):
    client = existing_client or coc.Client()
    try:
        if not existing_client: await client.login(coc_email, coc_password)
        group = await client.get_league_group(clan_tag)
        return group.clans
    finally:
        if not existing_client and 'client' in locals():
            await client.close()

async def _get_cwl_current_war_details_async(clan_tag, coc_email, coc_password, existing_client=None):
    client = existing_client or coc.Client()
    try:
        if not existing_client: await client.login(coc_email, coc_password)
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
        if not existing_client and 'client' in locals():
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
            if isinstance(result, Exception) or result is None or result[0] is None:
                df_predicted_opponent = pd.DataFrame([{"Erro": f"Não foi possível carregar a guerra de {opponent_name}."}])
            else:
                _, their_clan_df, their_opponent_df, their_clan_tag, _ = result
                df_predicted_opponent = their_clan_df if their_clan_tag == opponents[i].tag else their_opponent_df
            league_preview.append({'opponent_name': opponent_name, 'predicted_lineup': df_predicted_opponent})
            
        return df_our_clan, league_preview, our_war_summary.get('clan_name', 'Nosso Clã')
    finally:
        # --- CORREÇÃO APLICADA ---
        if 'client' in locals():
            await client.close()
