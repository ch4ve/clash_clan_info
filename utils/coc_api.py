# Em utils/coc_api.py, SUBSTITUA estas duas funções:

def generate_full_league_preview(our_clan_tag, coc_email, coc_password):
    return asyncio.run(_generate_full_league_preview_async(our_clan_tag, coc_email, coc_password))

async def _generate_full_league_preview_async(our_clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        
        # Helper interno para reutilizar o cliente logado
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
                    war_summary = {"clan_name": clan_side.name, "opponent_name": opponent_side.name} # Simplificado
                    return war_summary, df_clan, df_opponent, clan_side.tag
            return None, None, None, None

        our_war_summary, df_our_clan, _, _ = await _internal_get_war_details(our_clan_tag, client)
        if our_war_summary is None:
            return None, "Não foi possível carregar nossa guerra atual."
        
        all_clans = await _get_cwl_group_clans_async(our_clan_tag, coc_email, coc_password, existing_client=client)
        if not all_clans:
            return None, "Não foi possível carregar a lista de clãs do grupo."
            
        opponents = [clan for clan in all_clans if clan.tag != our_clan_tag]
        
        tasks = [_internal_get_war_details(opponent.tag, client) for opponent in opponents]
        scouting_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        league_preview = []
        for i, result in enumerate(scouting_results):
            opponent_name = opponents[i].name
            if isinstance(result, Exception) or result is None or result[0] is None:
                df_predicted_opponent = pd.DataFrame([{"Erro": f"Não foi possível carregar a guerra de {opponent_name}."}])
            else:
                _, their_clan_df, their_opponent_df, their_clan_tag = result
                df_predicted_opponent = their_clan_df if their_clan_tag == opponents[i].tag else their_opponent_df
            league_preview.append({'opponent_name': opponent_name, 'predicted_lineup': df_predicted_opponent})
            
        # --- CORREÇÃO AQUI: Retorna apenas os 2 valores que a página espera ---
        return df_our_clan, league_preview
    finally:
        if 'client' in locals() and not client.is_closed():
            await client.close()
