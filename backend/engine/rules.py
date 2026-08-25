from dataclasses import dataclass
from typing import Optional, List

@dataclass
class RuleResult:
    rule: str
    winner: Optional[str]
    score: int
    message: str

class Rule:
    def evaluate(self, context: dict) -> RuleResult:
        raise NotImplementedError("Subclasses must implement evaluate()")

class EloDominanceRule(Rule):
    def evaluate(self, context: dict) -> RuleResult:
        home_elo = context.get('home_elo', 1500)
        away_elo = context.get('away_elo', 1500)
        home_team = context.get('home_team', 'Local')
        away_team = context.get('away_team', 'Visita')
        
        diff = home_elo - away_elo
        
        if diff > 100:
            return RuleResult(rule="Elo Dominance", winner=home_team, score=8, message="Superioridad histórica aplastante (Elo)")
        elif diff < -100:
            return RuleResult(rule="Elo Dominance", winner=away_team, score=8, message="Superioridad histórica aplastante (Elo)")
        else:
            return RuleResult(rule="Elo Dominance", winner=None, score=3, message="Equipos muy parejos históricamente")

class PoissonLethalityRule(Rule):
    def evaluate(self, context: dict) -> RuleResult:
        home_xg = context.get('home_xg', 0.0)
        away_xg = context.get('away_xg', 0.0)
        home_team = context.get('home_team', 'Local')
        away_team = context.get('away_team', 'Visita')
        
        if home_xg > 2.0 and home_xg > away_xg + 0.5:
            return RuleResult(rule="Poisson Lethality", winner=home_team, score=10, message="Letalidad ofensiva muy alta proyectada (>2 xG)")
        elif away_xg > 2.0 and away_xg > home_xg + 0.5:
            return RuleResult(rule="Poisson Lethality", winner=away_team, score=10, message="Letalidad ofensiva muy alta proyectada (>2 xG)")
        elif home_xg > away_xg:
            return RuleResult(rule="Poisson Lethality", winner=home_team, score=5, message="Ligera ventaja ofensiva")
        elif away_xg > home_xg:
            return RuleResult(rule="Poisson Lethality", winner=away_team, score=5, message="Ligera ventaja ofensiva")
        else:
            return RuleResult(rule="Poisson Lethality", winner=None, score=3, message="Potencia ofensiva equilibrada")

class MachineLearningConsensusRule(Rule):
    def evaluate(self, context: dict) -> RuleResult:
        ml_winner = context.get('ml_winner')
        poisson_winner = context.get('poisson_winner')
        
        if ml_winner and ml_winner == poisson_winner:
            return RuleResult(rule="ML Consensus", winner=ml_winner, score=15, message="Consenso Absoluto: IA y Matemáticas coinciden")
        elif ml_winner:
            return RuleResult(rule="ML Consensus", winner=ml_winner, score=5, message="La IA predice este ganador (Sin consenso Poisson)")
        else:
            return RuleResult(rule="ML Consensus", winner=None, score=0, message="Sin consenso de Inteligencia Artificial")

class RecentFormRule(Rule):
    def evaluate(self, context: dict) -> RuleResult:
        hist = context.get('historical_context')
        home_team = context.get('home_team', 'Local')
        away_team = context.get('away_team', 'Visita')
        
        if not hist or not hist.get('home') or not hist.get('away'):
            return RuleResult(rule="Recent Form", winner=None, score=0, message="Sin datos históricos recientes")
            
        home_form_str = hist['home'].get('form', '')
        away_form_str = hist['away'].get('form', '')
        
        if home_form_str:
            home_pts = home_form_str.count('W')*3 + home_form_str.count('D')*1
        else:
            home_pts = hist['home'].get('form_points', 0)
            
        if away_form_str:
            away_pts = away_form_str.count('W')*3 + away_form_str.count('D')*1
        else:
            away_pts = hist['away'].get('form_points', 0)
        
        diff = home_pts - away_pts
        if diff >= 6:
            return RuleResult(rule="Recent Form", winner=home_team, score=7, message="Excelente racha reciente (Local)")
        elif diff <= -6:
            return RuleResult(rule="Recent Form", winner=away_team, score=7, message="Excelente racha reciente (Visita)")
        elif diff > 0:
            return RuleResult(rule="Recent Form", winner=home_team, score=3, message="Mejor momento anímico")
        elif diff < 0:
            return RuleResult(rule="Recent Form", winner=away_team, score=3, message="Mejor momento anímico")
        else:
            return RuleResult(rule="Recent Form", winner=None, score=1, message="Momentos similares")

class GoalsScoredRule(Rule):
    def evaluate(self, context: dict) -> RuleResult:
        hist = context.get('historical_context')
        home_team = context.get('home_team', 'Local')
        away_team = context.get('away_team', 'Visita')
        
        if not hist or not hist.get('home') or not hist.get('away'):
            return RuleResult(rule="Offensive Power", winner=None, score=0, message="Sin datos de goles")
            
        home_goals = hist['home'].get('avg_goals_scored', context.get('home_xg', 0.0))
        away_goals = hist['away'].get('avg_goals_scored', context.get('away_xg', 0.0))
        
        if home_goals >= 2.0 and home_goals > away_goals + 0.5:
            return RuleResult(rule="Offensive Power", winner=home_team, score=5, message="Ataque Demoledor (>2 goles/partido)")
        elif away_goals >= 2.0 and away_goals > home_goals + 0.5:
            return RuleResult(rule="Offensive Power", winner=away_team, score=5, message="Ataque Demoledor (>2 goles/partido)")
        else:
            return RuleResult(rule="Offensive Power", winner=None, score=0, message="Ofensivas sin ventajas abrumadoras")

ALL_PREMATCH_RULES = [
    EloDominanceRule(),
    PoissonLethalityRule(),
    MachineLearningConsensusRule(),
    RecentFormRule(),
    GoalsScoredRule()
]
