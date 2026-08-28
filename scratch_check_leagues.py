import json
import sqlite3

try:
    with open('backend/team_stats_db.json', 'r', encoding='utf-8') as f:
        stats_db = json.load(f)
    stats_team_ids = set(int(k) for k in stats_db.keys())

    conn = sqlite3.connect('backend/tipster.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT league_id, home_team_id FROM historical_matches')
    league_team_map = {}
    for league_id, team_id in cursor.fetchall():
        if league_id not in league_team_map:
            league_team_map[league_id] = set()
        league_team_map[league_id].add(team_id)

    # Let's map league_id to names based on ALL_TRACKED_LEAGUES from seed_ligas
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

    print("--- ESTADO DE LIGAS ---")
    for name, lid in ALL_TRACKED_LEAGUES.items():
        if lid in league_team_map:
            league_teams = league_team_map[lid]
            seeded_count = sum(1 for tid in league_teams if tid in stats_team_ids)
            total = len(league_teams)
            if seeded_count >= total * 0.8: # If 80%+ teams seeded
                print(f"[X] {name}")
            else:
                print(f"[ ] {name} ({seeded_count}/{total})")
        else:
            print(f"[ ] {name} (0/0)")

except Exception as e:
    print(e)
