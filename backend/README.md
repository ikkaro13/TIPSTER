# API Endpoints - Tipster / Athena

| Método | Endpoint | Descripción | Body / Parámetros | Respuesta |
| --- | --- | --- | --- | --- |
| GET | `/` | Health check del servidor | Ninguno | `{"status": "ok", ...}` |
| GET | `/api/portfolio` | Obtiene el estado actual del bankroll y ledger de apuestas | Ninguno | `{"bankroll": float, "initial_bankroll": float, "bets": list}` |
| POST | `/api/portfolio/reset` | Reinicia el bankroll a un monto inicial | `{"new_amount": float}` | `{"status": "success", "new_bankroll": float}` |
| POST | `/api/portfolio/bet` | Registra una nueva apuesta en el ledger | `{"match_id": str, "pick": str, "odds": float, "stake": float, "evidence_snapshot": str, "bet_type": str}` | `{"status": "success", "bet_id": str, "new_bankroll": float}` |
| POST | `/api/portfolio/settle/{bet_id}` | Cierra una apuesta (WON/LOST/REFUND) y ajusta bankroll | `{"result": "WON" | "LOST" | "REFUND"}` | `{"status": "success", "new_bankroll": float}` |
| POST | `/api/portfolio/reopen/{bet_id}` | Reabre una apuesta cerrada, deshaciendo los cambios en bankroll | Ninguno | `{"status": "success", "new_bankroll": float}` |
| PUT | `/api/portfolio/bets/{bet_id}/odds` | Actualiza la cuota de una apuesta (abierta o cerrada) y recalcula ganancias | `{"odds": float}` | `{"status": "success", "new_bankroll": float}` |
| DELETE | `/api/portfolio/bets/{bet_id}` | Elimina una apuesta del ledger por completo | Ninguno | `{"status": "success", "new_bankroll": float}` |
| POST | `/api/portfolio/autopsy` | Corre Autopsia: evalúa resultados reales de apuestas abiertas vía API | Ninguno | `{"status": "success", "resolved_count": int}` |
| GET | `/api/portfolio/audit-log` | Devuelve el registro de auditoría atómica del Bankroll | `?limit=50` | `{"audit_log": list}` |
| GET | `/api/portfolio/lab` | Extrae estadísticas de rentabilidad por mercado/liga/pick | Ninguno | `{"por_mercado": dict, "por_liga": dict, ...}` |
| GET | `/api/shadow/status` | Muestra el estado de cuarentena (Shadow Mode) de cada mercado | Ninguno | `{"shadow_markets": list}` |
| POST | `/api/argos/toggle` | Activa/desactiva el rastreador en vivo Argos | Ninguno | `{"status": "success", "argos_active": bool}` |
| GET | `/api/argos/status` | Devuelve el estado actual de Argos | Ninguno | `{"argos_active": bool}` |
| GET | `/api/matches` | Devuelve los partidos principales programados para hoy | Ninguno | `list de diccionarios con info de partidos` |
| GET | `/api/calendar` | Obtiene los partidos de un día específico (YYYY-MM-DD) | `?date=YYYY-MM-DD` | `list de partidos` |
| POST | `/api/prematch-insight` | Calcula probabilidades base y contexto histórico pre-partido | `{"homeTeam": str, "awayTeam": str, "match_id": str}` | `{"probs": dict}` |
| POST | `/api/recalculate-hermes` | Oráculo Hermes: Análisis humano con contexto profundo y xG | `{"homeTeam": str, "awayTeam": str, ...}` | `{"hermes": dict}` |
| GET | `/api/athena-live/{match_id}` | Actualización en vivo (minuto, marcador) para un partido | Ninguno | `dict con live data` |
| POST | `/api/live-analysis` | Análisis in-play basado en eventos en vivo (Argos) | `{"match_id": str, "homeTeam": str, "awayTeam": str, "minute": int, "homeGoals": int, "awayGoals": int}` | `{"analysis": dict}` |
| POST | `/api/ares/calculate` | Calculadora de Valor Esperado (EV) y Kelly para apuestas simples | `{"homeTeam": str, "awayTeam": str, "bookmaker_odds": dict}` | `{"ares": dict}` |
| GET | `/api/chronos/scan-day` | Motor Delfos: Escanea todos los partidos del día buscando Value Bets | `?date=YYYY-MM-DD` | `list de picks recomendados` |
| GET | `/api/delfos/historial` | Historial de apuestas de Delfos escaneadas automáticamente | Ninguno | `{"delfos_picks": list}` |
| POST | `/api/autotune/run` | Corre Random Forest para calibrar umbrales matemáticos | Ninguno | `{"status": "success", "new_params": dict}` |
