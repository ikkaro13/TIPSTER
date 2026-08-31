import re

with open('backend/autopsy_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_logic = '''                if is_won is not None:
                    new_status = 'WON' if is_won else 'LOST'
                    settle_bet(bet_id, new_status)
                    
                    # Append to corpus
                    if evidence_str:
                        try:
                            snap = json.loads(evidence_str)
                            record = {
                                "bet_id": bet_id,
                                "match_id": match_id,
                                "home_team": home_team,
                                "away_team": away_team,
                                "pick": pick,
                                "result": new_status,
                                "evidence_snapshot": snap
                            }
                            with open(CORPUS_FILE, 'a', encoding='utf-8') as cf:
                                cf.write(json.dumps(record) + "\\n")
                        except:
                            pass
                            
                    resolved_count += 1'''

new_logic = '''                if is_won is not None:
                    new_status = 'WON' if is_won else 'LOST'
                    settle_bet(bet_id, new_status)
                    
                    # Sync with delfos_picks
                    conn2 = get_db_connection()
                    try:
                        conn2.execute("UPDATE delfos_picks SET resultado = ?, es_correcto = ?, goles_home = ?, goles_away = ? WHERE fixture_id = ? AND pick = ?",
                                      (new_status, 1 if is_won else 0, home_goals, away_goals, match_id, pick))
                        conn2.commit()
                    except Exception as e:
                        pass
                    finally:
                        conn2.close()
                    
                    # Append to corpus avoiding duplicates
                    if evidence_str:
                        try:
                            import os
                            snap = json.loads(evidence_str)
                            record = {
                                "bet_id": bet_id,
                                "match_id": match_id,
                                "home_team": home_team,
                                "away_team": away_team,
                                "pick": pick,
                                "result": new_status,
                                "evidence_snapshot": snap
                            }
                            
                            # Check duplicates
                            exists = False
                            if os.path.exists(CORPUS_FILE):
                                with open(CORPUS_FILE, 'r', encoding='utf-8') as cf:
                                    for line in cf:
                                        if f'"bet_id": "{bet_id}"' in line:
                                            exists = True
                                            break
                            if not exists:
                                with open(CORPUS_FILE, 'a', encoding='utf-8') as cf:
                                    cf.write(json.dumps(record) + "\\n")
                        except:
                            pass
                            
                    resolved_count += 1'''

content = content.replace(old_logic, new_logic)
with open('backend/autopsy_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
