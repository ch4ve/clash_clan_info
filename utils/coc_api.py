import pandas as pd
import coc
import asyncio
from collections import defaultdict
from .loop_manager import loop_manager

# --- FUNÇÕES SÍNCRONAS (WRAPPERS) ---
def get_clan_data(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(_get_clan_data_async(clan_tag, coc_email, coc_password))

def get_current_war_data(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(_get_current_war_data_async(clan_tag, coc_email, coc_password))

def get_cwl_current_war_details(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(_get_cwl_current_war_details_async(clan_tag, coc_email, coc_password))

def get_cwl_group_clans(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(_get_cwl_group_clans_async(clan_tag, coc_email, coc_password))

def generate_full_league_preview(our_clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(_generate_full_league_preview_async(our_clan_tag, coc_email, coc_password))


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
        if 'client' in locals() and not client.is_closed(): await client.close()

async def _get_current_war_data_async(clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        war = await client.get_current_war(clan_tag)
        opponent_map = {opponent.tag: opponent for opponent in war.opponent.members}
        attacks_data = []
        for member in war.clan.members:
            ataques_feitos = len(member.attacks)
            estrelas_atk1, cv_inimigo_atk1 = 0, "-"
            if ataques_feitos >= 1:
                atk1 = member.attacks[0]; estrelas_atk1 = atk1.stars
                inimigo1 = opponent_map.get(atk1.defender_tag)
                if inimigo1: cv_inimigo_atk1 = inimigo1.town_hall
            estrelas_atk2, cv_inimigo_atk2 = 0, "-"
            if ataques_feitos == 2:
                atk2 = member.attacks[1]; estrelas_atk2 = atk2.stars
                inimigo2 = opponent_map.get(atk2.defender_tag)
                if inimigo2: cv_inimigo_atk2 = inimigo2.town_hall
            attacks_data.append({'Posição': member.map_position, 'Nome': member.name, 'Ataques Feitos': ataques_feitos, 'Estrelas Atk 1': estrelas_atk1, 'CV Inimigo Atk 1': cv_inimigo_atk1, 'Estrelas Atk 2': estrelas_atk2, 'CV Inimigo Atk 2': cv_inimigo_atk2})
        df_attacks = pd.DataFrame(attacks_data)
        if not df_attacks.empty:
            df_attacks['Estrelas Totais'] = df_attacks['Estrelas Atk 1'] + df_attacks['Estrelas Atk 2']
        return df_attacks.sort_values(by='Posição', ascending=True)
    except coc.NotFound:
        return None
    finally:
        if 'client' in locals() and not client.is_closed(): await client.close()

async def _get_cwl_group_clans_async(clan_tag, coc_email, coc_password, existing_client=None):
    client = existing_client or coc.Client()
    try:
        if not existing_client: await client.login(coc_email, coc_password)
        group = await client.get_league_group(clan_tag)
        return group.clans
    finally:
        if not existing_client and 'client' in locals() and not client.is_closed(): await client.close()

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
                war_summary = {"clan_name": clan_side.name, "opponent_name": opponent_side.name}
                return war_summary, df_clan, df_opponent
        return None, None, None
    finally:
        if not existing_client and 'client' in locals() and not client.is_closed(): await client.close()

async def _generate_full_league_preview_async(our_clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        our_war_summary, df_our_clan, _ = await _get_cwl_current_war_details_async(our_clan_tag, coc_email, coc_password, existing_client=client)
        if our_war_summary is None:
            return None, "Não foi possível carregar nossa guerra atual."
        
        all_clans = await _get_cwl_group_clans_async(our_clan_tag, coc_email, coc_password, existing_client=client)
        if not all_clans:
            return None, "Não foi possível carregar a lista de clãs do grupo."
            
        opponents = [clan for clan in all_clans if clan.tag != our_clan_tag]
        tasks = [_get_cwl_current_war_details_async(opponent.tag, coc_email, coc_password, existing_client=client) for opponent in opponents]
        scouting_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        league_preview = []
        for i, result in enumerate(scouting_results):
            opponent_name = opponents[i].name
            if isinstance(result, Exception) or result is None:
                df_predicted_opponent = pd.DataFrame([{"Erro": f"Não foi possível carregar a guerra de {opponent_name}."}])
            else:
                _, their_clan_df, their_opponent_df = result
                # Precisamos descobrir qual dos dois DataFrames é o do oponente que buscamos
                # Essa lógica precisa ser melhorada, mas por enquanto assumimos que o primeiro é o clã e o segundo o oponente
                # A forma correta seria a função _get_cwl_current_war_details_async retornar as tags também
                df_predicted_opponent = their_clan_df # Assumindo que o primeiro DataFrame é o do clã buscado
            league_preview.append({'opponent_name': opponent_name, 'predicted_lineup': df_predicted_opponent})
            
        return df_our_clan, league_preview, our_war_summary.get('clan_name', 'Nosso Clã')
    finally:
        if 'client' in locals() and not client.is_closed(): await client.close()

# As outras funções que não estão sendo usadas ativamente (histórico, resumo cwl) foram omitidas para focar na estabilidade.
