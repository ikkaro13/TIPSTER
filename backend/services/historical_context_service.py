import api_football_engine

class HistoricalContextService:
    def __init__(self):
        pass

    def build_context(self, fixture_id: str):
        """Construye el contexto histórico pre-match de los equipos"""
        
        # 1. Obtener IDs
        details = api_football_engine.get_fixture_details(fixture_id)
        if not details or "teams" not in details:
            return None
            
        home_id = details["teams"]["home"]["id"]
        away_id = details["teams"]["away"]["id"]
        
        # 2. Bajar los últimos 10 partidos
        home_fixtures = api_football_engine.get_team_historical_stats(home_id, last_n=10)
        away_fixtures = api_football_engine.get_team_historical_stats(away_id, last_n=10)
        
        # 3. Procesar estadísticas
        home_stats = self._process_team_fixtures(home_fixtures, home_id)
        away_stats = self._process_team_fixtures(away_fixtures, away_id)
        
        return {
            "home": home_stats,
            "away": away_stats
        }

    def _process_team_fixtures(self, fixtures, team_id):
        if not fixtures:
            # Fallback
            return {
                "avg_goals_scored": 1.25,
                "avg_goals_conceded": 1.25,
                "form_points": 5, # Asumiendo 10 pts máx (para 10 juegos)
                "btts_percent": 50.0,
                "over_2_5_percent": 50.0,
                "matches_played": 0
            }
            
        goals_scored = 0
        goals_conceded = 0
        points = 0
        btts_count = 0
        over_2_5_count = 0
        
        valid_matches = 0
        
        for f in fixtures:
            goals = f.get("goals", {})
            gh = goals.get("home")
            ga = goals.get("away")
            
            if gh is None or ga is None:
                continue
                
            valid_matches += 1
            
            # Identificar si el equipo fue local o visita
            is_home = f["teams"]["home"]["id"] == team_id
            
            scored = gh if is_home else ga
            conceded = ga if is_home else gh
            
            goals_scored += scored
            goals_conceded += conceded
            
            if scored > conceded:
                points += 3
            elif scored == conceded:
                points += 1
                
            if scored > 0 and conceded > 0:
                btts_count += 1
                
            if (scored + conceded) > 2.5:
                over_2_5_count += 1
                
        if valid_matches == 0:
            return self._process_team_fixtures([], team_id) # Call fallback
            
        return {
            "avg_goals_scored": round(goals_scored / valid_matches, 2),
            "avg_goals_conceded": round(goals_conceded / valid_matches, 2),
            "form_points": points, # Puntos totales en últimos partidos
            "btts_percent": round((btts_count / valid_matches) * 100, 1),
            "over_2_5_percent": round((over_2_5_count / valid_matches) * 100, 1),
            "matches_played": valid_matches
        }
