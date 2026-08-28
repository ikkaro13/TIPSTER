import json
import sqlite3

try:
    with open('backend/team_stats_db.json', 'r', encoding='utf-8') as f:
        stats_db = json.load(f)
        
    seeded_leagues = set()
    for tid, tdata in stats_db.items():
        league_id = tdata.get("league")
        if league_id:
            seeded_leagues.add(int(league_id))
            
    ALL_TRACKED_LEAGUES = {
        "Premier League": 39, "La Liga": 140, "Serie A": 135, "Bundesliga": 78, "Ligue 1": 61,
        "Liga MX": 262, "MLS": 253, "Brasileirao": 71, "Primera Div Argentina": 128, "Primera A Colombia": 239,
        "Liga Expansion MX": 263, "Primera Nacional Arg": 129,
        "Championship": 40, "Serie B": 136, "Segunda Division": 141,
        "Eredivisie": 88, "Eerste Divisie": 89, "Primeira Liga": 94, "Süper Lig": 203, "Scottish Premiership": 179, "Jupiler Pro League": 144,
        "Eliteserien": 103, "Allsvenskan": 113, "Superettan": 114, "Veikkausliiga": 121, "Ekstraklasa": 106, "SuperLiga": 283, "Parva Liga": 172,
        "J1 League": 98, "J2 League": 99, "K League 1": 292, "Saudi Pro League": 307, "A-League": 188,
        "Super League Suiza": 207, "Superliga Dinamarca": 119, "Super League Grecia": 197, "Division Profesional": 305, "Liga 1 Peru": 281
    }
    
    # Let's count how many teams are seeded for A-League (188)
    aleague_teams = sum(1 for tid, tdata in stats_db.items() if tdata.get("league") == 188)
    
    # If a league has > 0 teams, we consider it seeded for this check, EXCEPT A-League which is partial
    for name, lid in ALL_TRACKED_LEAGUES.items():
        if lid in seeded_leagues:
            print(f"[x] {name}")
        else:
            print(f"[ ] {name}")
            
    print(f"A-League teams downloaded: {aleague_teams}")
    
except Exception as e:
    print(e)
