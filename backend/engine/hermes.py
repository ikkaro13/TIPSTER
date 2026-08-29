from engine.rules import ALL_PREMATCH_RULES

class ValueAggregator:
    def __init__(self, min_edge=3.0, min_prob_threshold=52.0):
        self.min_edge = min_edge
        self.min_prob_threshold = min_prob_threshold

    def evaluate_value(self, current_pick, current_confidence, context):
        odds = context.get('odds', {})
        probs = context.get('probs', {})
        
        if not odds or not probs:
            return current_pick, current_confidence
            
        # Mapeo de predicciones a claves de odds y probs
        market_map = {
            context.get('home_team'): "home",
            "Empate": "draw",
            context.get('away_team'): "away",
            "Over 2.5 Goles (Alta Intensidad)": "over_2_5",
            "Over 0.5 Goles 1T (Arranque Rápido)": "over_0_5_ht", # Asumiendo que pudiese existir, si no, lo ignoramos
            "Ambos Anotan - SÍ": "btts_yes",
            "Ambos Anotan - NO": "btts_no",
            "Under 2.5 Goles (Partido Cerrado)": "under_2_5",
            "Doble Oportunidad (1X)": "dc_1x",
            "Doble Oportunidad (X2)": "dc_x2",
            "DNB (Local)": "dnb_home",
            "DNB (Visita)": "dnb_away",
        }
        
        market_map_inverse = {v: k for k, v in market_map.items()}
        
        # Calcular todos los edges disponibles
        edges = {}
        for market_desc, key in market_map.items():
            if key in odds and key in probs:
                o = float(odds[key])
                if o < 1.60:
                    continue # REGLA ESTRICTA: No consideramos apuestas con momios menores a 1.60
                
                p = float(probs[key]) / 100.0
                if o > 1.0:
                    edge = (p * o) - 1
                    edges[market_desc] = edge * 100

        if not edges:
            return current_pick, current_confidence

        # Revisar si el pick actual tiene buen edge y buena probabilidad
        current_edge = edges.get(current_pick, -100)
        
        if current_edge >= self.min_edge and current_confidence >= self.min_prob_threshold:
            return f"{current_pick} (Value Bet: +{current_edge:.1f}%)", current_confidence
            
        # Si el pick actual no sirve, buscamos el mercado MÁS PROBABLE que tenga un Edge positivo (>= min_edge)
        # Y que cumpla con el filtro estricto de confianza del usuario (>= min_prob_threshold)
        valid_markets = {}
        for m, e in edges.items():
            m_key = market_map.get(m)
            p = float(probs.get(m_key, 0)) if m_key else 0
            if e >= self.min_edge and p * 100.0 >= self.min_prob_threshold:
                valid_markets[m] = e
        
        if valid_markets:
            best_market = None
            best_market_prob = -1
            best_market_edge = 0
            
            for m_desc, edge in valid_markets.items():
                m_key = market_map.get(m_desc)
                p = float(probs.get(m_key, 0)) if m_key else 0
                if p > best_market_prob:
                    best_market_prob = p
                    best_market = m_desc
                    best_market_edge = edge
                    
            return f"{best_market} (Pivote Seguro: +{best_market_edge:.1f}%)", int(best_market_prob)
            
        # Si NO HAY NINGÚN MERCADO individual con valor, armamos una Combinada (SGP)
        # 1. Buscar lo más probable de 1X2 (Incluyendo Doble Oportunidad)
        p_home = float(probs.get('home', 0))
        p_draw = float(probs.get('draw', 0))
        p_away = float(probs.get('away', 0))
        
        home_team = context.get('home_team', 'Local')
        away_team = context.get('away_team', 'Visita')
        
        winner_probs = {
            f"Gana {home_team}": p_home,
            "Empate": p_draw,
            f"Gana {away_team}": p_away,
            f"Doble Oport. ({home_team} o Empate)": min(p_home + p_draw, 99.0),
            f"Doble Oport. ({away_team} o Empate)": min(p_away + p_draw, 99.0),
            f"Cualquiera Gana ({home_team} o {away_team})": min(p_home + p_away, 99.0)
        }
        best_winner_desc = max(winner_probs, key=winner_probs.get)
        best_winner_prob = winner_probs[best_winner_desc] / 100.0

        # 2. Buscar lo más probable de Goles
        goals_probs = {
            "Más de 1.5 Goles": float(probs.get('over_1_5', 0)),
            "Menos de 3.5 Goles": float(probs.get('under_3_5', 0)),
            "Más de 2.5 Goles": float(probs.get('over_2_5', 0)),
            "Ambos Anotan (SÍ)": float(probs.get('btts_yes', 0)),
            "Ambos Anotan (NO)": float(probs.get('btts_no', 0))
        }
        goals_probs = {k: v for k, v in goals_probs.items() if v > 0}
        
        if goals_probs and best_winner_prob > 0.35:
            best_goal_desc = max(goals_probs, key=goals_probs.get)
            best_goal_prob = goals_probs[best_goal_desc] / 100.0
            
            # Combinar asumiendo independencia para la cuota base
            combined_prob = best_winner_prob * best_goal_prob
            
            
            if combined_prob > 0.25: # Al menos 25% de probabilidad conjunta (Cuotas ~4.00 o menores)
                min_odds = (1.0 + (self.min_edge / 100.0)) / combined_prob
                return f"👑 PARLAY (Crear Apuesta): {best_winner_desc} + {best_goal_desc} (Busca cuota > {min_odds:.2f})", int(combined_prob * 100)
                
        return "NO BET (Sin Valor Matemático > 3%)", 0

    def evaluate_safe(self, current_pick, confidence, context):
        """
        El 'Ladrillo'. Busca el mercado con mayor probabilidad absoluta que tenga una cuota mínima de 1.60.
        Ignora por completo el Edge matemático.
        """
        odds = context.get('odds', {})
        probs = context.get('probs', {})
        
        market_map = {
            "Gana Local": "home",
            "Empate": "draw",
            "Gana Visita": "away",
            "Mǭs de 1.5 Goles": "over_1_5",
            "Mǭs de 2.5 Goles": "over_2_5",
            "Menos de 3.5 Goles": "under_3_5",
            "Ambos Anotan (S?)": "btts_yes",
            "Ambos Anotan (NO)": "btts_no",
            "Menos de 2.5 Goles": "under_2_5",
            "Doble Oportunidad (1X)": "dc_1x",
            "Doble Oportunidad (X2)": "dc_x2",
            "DNB (Local)": "dnb_home",
            "DNB (Visita)": "dnb_away"
        }
        valid_safe_markets = {}
        for market_desc, key in market_map.items():
            if key in odds and key in probs:
                try:
                    o = float(odds[key])
                    p = float(probs[key])
                except (ValueError, TypeError):
                    continue
                
                # REGLA DEL LADRILLO: Cuota mínima de 1.60
                if o >= 1.60:
                    # Verificar que el edge no sea demasiado negativo (> -5%)
                    # Evita recomendar apuestas con overround muy alto donde la casa siempre gana
                    implied_edge = (p / 100.0) * o - 1
                    if implied_edge > -0.05:
                        valid_safe_markets[market_desc] = p
                    
        if not valid_safe_markets:
            return "NO HAY SAFE PICK (Ningún mercado seguro >= 1.60)", 0
            
        best_safe_desc = max(valid_safe_markets, key=valid_safe_markets.get)
        best_safe_prob = valid_safe_markets[best_safe_desc]
        
        return f"{best_safe_desc} (Cuota >= 1.60)", int(best_safe_prob)


class EvidenceAggregator:
    def __init__(self):
        # Asignación de pesos dinámicos por regla
        self.weights = {
            "Elo Dominance": 1.0,
            "Poisson Lethality": 1.5,
            "ML Consensus": 2.0,
            "Recent Form": 1.5,
            "Offensive Power": 1.2
        }
        self.value_aggregator = ValueAggregator(min_edge=3.0)

    def aggregate(self, results, context):
        home_team = context.get('home_team')
        away_team = context.get('away_team')
        
        home_weighted_score = 0
        away_weighted_score = 0
        total_possible_weight = 0

        for r in results:
            rule_name = r['rule']
            weight = self.weights.get(rule_name, 1.0)
            score = r['score']
            
            total_possible_weight += (5 * weight)
            
            if r['winner'] == home_team:
                home_weighted_score += (score * weight)
            elif r['winner'] == away_team:
                away_weighted_score += (score * weight)

        is_conflicted = False
        if home_weighted_score > 0 and away_weighted_score > 0:
            ratio = min(home_weighted_score, away_weighted_score) / max(home_weighted_score, away_weighted_score)
            if ratio > 0.6:
                is_conflicted = True

        total_actual_score = home_weighted_score + away_weighted_score
        
        final_pick = "Empate"
        confidence = 50

        if total_actual_score > 0:
            if home_weighted_score > away_weighted_score:
                final_pick = home_team
                confidence = min(int((home_weighted_score / total_possible_weight) * 100), 100)
            elif away_weighted_score > home_weighted_score:
                final_pick = away_team
                confidence = min(int((away_weighted_score / total_possible_weight) * 100), 100)
                
        if is_conflicted:
            confidence = int(confidence * 0.5)
            
            home_xg = context.get('home_xg', 0)
            away_xg = context.get('away_xg', 0)
            total_xg = home_xg + away_xg
            
            if total_xg >= 3.0:
                final_pick = "Over 2.5 Goles (Alta Intensidad)"
                confidence = min(int((total_xg / 3.5) * 85), 95)
            elif total_xg >= 2.2 and home_xg >= 1.1 and away_xg >= 1.1:
                final_pick = "Ambos Anotan - SÍ"
                confidence = 80
            elif total_xg >= 2.0:
                final_pick = "Over 0.5 Goles 1T (Arranque Rápido)"
                confidence = 75
            elif total_xg <= 1.5:
                final_pick = "Under 2.5 Goles (Partido Cerrado)"
                confidence = 85
            elif home_xg < 0.8 or away_xg < 0.8:
                final_pick = "Ambos Anotan - NO"
                confidence = 78
            else:
                final_pick = "NO BET (Conflicto Extremo y Sin Tendencia)"
                confidence = 0

        # Paso Final: Evaluar Apuestas de Valor si existen cuotas
        value_pick, value_confidence = final_pick, confidence
        safe_pick, safe_confidence = "NO BET", 0
        
        if 'odds' in context and 'probs' in context:
            # Francotirador (Valor)
            value_pick, value_confidence = self.value_aggregator.evaluate_value(final_pick, confidence, context)
            # Ladrillo (Seguro/Banker)
            safe_pick, safe_confidence = self.value_aggregator.evaluate_safe(final_pick, confidence, context)

        return {
            "value_pick": value_pick,
            "value_confidence": value_confidence,
            "safe_pick": safe_pick,
            "safe_confidence": safe_confidence,
            "total_score": round(total_actual_score, 1),
            "is_conflicted": is_conflicted
        }

class Hermes:
    def __init__(self):
        self.rules = ALL_PREMATCH_RULES
        self.aggregator = EvidenceAggregator()

    def analyze(self, context: dict):
        # Sanitizar strings vacíos
        for k, v in context.get('odds', {}).items():
            if v == "" or v is None:
                context['odds'][k] = 0
                
        for k, v in context.get('probs', {}).items():
            if v == "" or v is None:
                context['probs'][k] = 0
                
        results = []
        
        for rule in self.rules:
            result = rule.evaluate(context)
            results.append({
                "rule": result.rule,
                "winner": result.winner,
                "score": result.score,
                "message": result.message
            })

        aggregation = self.aggregator.aggregate(results, context)
        
        # Stake Engine (1 Unidad = 100 por defecto, pero dejaremos que el frontend decida el valor base de la unidad)
        # Aquí solo sugerimos las Unidades en base al pick de Valor
        conf = aggregation["value_confidence"]
        if "NO BET" in aggregation["value_pick"]:
            recommended_units = 0
        elif conf >= 80:
            recommended_units = 2.0
        elif conf >= 65:
            recommended_units = 1.5
        elif conf >= 50:
            recommended_units = 1.0
        else:
            recommended_units = 0.5
            
        return {
            "pick": aggregation["value_pick"], # Por retrocompatibilidad con componentes antiguos si los hay
            "confidence": aggregation["value_confidence"],
            "value_pick": aggregation["value_pick"],
            "value_confidence": aggregation["value_confidence"],
            "safe_pick": aggregation["safe_pick"],
            "safe_confidence": aggregation["safe_confidence"],
            "total_score": aggregation["total_score"],
            "is_conflicted": aggregation["is_conflicted"],
            "recommended_units": recommended_units,
            "rules_evaluated": results
        }
