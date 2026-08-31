"use client";

import { useEffect, useState } from "react";

let API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
if (typeof window !== "undefined") {
  API_BASE = `http://${window.location.hostname}:8000`;
}

interface Portfolio {
  bankroll: number;
  initial_bankroll: number;
  bets: any[];
}

interface OddItem { price: number; bookie: string; }
interface OddsData {
  home: OddItem; draw: OddItem; away: OddItem;
  over_1_5: OddItem; under_1_5: OddItem;
  over_2_5: OddItem; under_2_5: OddItem;
  over_3_5: OddItem; under_3_5: OddItem;
  btts_yes: OddItem; btts_no: OddItem;
  home_minus_1_5: OddItem; away_minus_1_5: OddItem;
}

interface Match {
  id: string; league: string; homeTeam: string; awayTeam: string;
  startTime: string; status: string; score: string; minute: string;
  smart_money_alert: boolean;
  arbitrage_alert: { 
    active: boolean; roi_percent: number; margin: number;
    home: { bookie: string; price: number };
    draw: { bookie: string; price: number };
    away: { bookie: string; price: number };
  };
  odds: OddsData;
  analysis: { 
    main_line: { pick: string; prob: number; odds: number; edge: number; kelly_percent: number; bookmaker?: string; } | null;
    medium_risk: { pick: string; prob: number; odds: number; edge: number; kelly_percent: number; bookmaker?: string; } | null;
    dreamer: { pick: string; prob: number; fair_odds: number; odds?: number; } | null;
    ultra: { pick: string; prob: number; fair_odds: number; } | null;
    corners_alert?: { pick: string; prob: number; fair_odds: number; } | null;
    player_prop?: { player: string; pick: string; prob: number; fair_odds: number; } | null;
    is_ensembled?: boolean;
  };
}

const MatchCard = ({ initialMatch, onPlaceBet }: { initialMatch: Match, onPlaceBet: any }) => {
  const [match, setMatch] = useState(initialMatch);
  const [athenaData, setAthenaData] = useState<any>(null);

  // Hook para cargar datos reales de ATHENA automáticamente y refrescar en vivo
  useEffect(() => {
    const fetchAthena = async () => {
      try {
        const athRes = await fetch(`${API_BASE}/api/athena-live/${match.id}`);
        const athData = await athRes.json();
        if (athData.athena) {
          setAthenaData(athData.athena);
          if (athData.live_data) {
             setMatch(prev => ({
                ...prev, 
                score: athData.live_data.score || prev.score,
                minute: athData.live_data.minute?.toString() || prev.minute
             }));
          }
        }
      } catch (e) {
        console.error("Athena Live Error:", e);
      }
    };
    
    // Cargar inicial
    fetchAthena();
    
    // Refrescar cada 60 segundos si el partido está en vivo
    let interval: NodeJS.Timeout;
    if (match.status === 'LIVE') {
      interval = setInterval(fetchAthena, 60000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [match.id, match.status]);


  const liveMinute = parseInt(match.minute) || 0;

  return (
    <div className="match-card" style={{padding: '2rem'}}>
      <div className="card-header" style={{borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '1rem'}}>
        <span className="league-badge" style={{background: '#3b82f6', color: 'white'}}>{match.league}</span>
        <div style={{display: 'flex', gap: '0.8rem', alignItems: 'center'}}>
          {match.analysis?.is_ensembled && (
            <span style={{background: 'linear-gradient(90deg, #9333ea, #db2777)', color: 'white', padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.7rem', fontWeight: 800, boxShadow: '0 0 10px rgba(219, 39, 119, 0.4)'}}>
              🤖 IA ENSEMBLED
            </span>
          )}
          <span className={`time-badge ${liveMinute > 0 ? "live" : ""}`}>
            {liveMinute > 0 ? `${liveMinute}' EN VIVO` : match.startTime}
          </span>
        </div>
      </div>
      
                <div className="match-teams" style={{fontSize: '2.2rem', padding: '1.5rem 0 1.5rem 0'}}>
                  <div className="team">{match.homeTeam || "Equipo 1"}</div>
                  <div className="score-container" style={{color: '#3b82f6'}}>{(match.score || "-").replace('-', ' - ')}</div>
                  <div className="team">{match.awayTeam || "Equipo 2"}</div>
                </div>

                {match.smart_money_alert && (
        <div style={{background: '#fee2e2', color: '#b91c1c', padding: '0.6rem', borderRadius: '8px', textAlign: 'center', marginBottom: '1rem', fontWeight: 600, fontSize: '0.9rem', border: '1px solid #fca5a5'}}>
          🚨 ALERTA INSTITUCIONAL: Dinero Inteligente Detectado (Caída abrupta de Cuota)
        </div>
      )}
      
      {athenaData?.goal_alert && (
        <div style={{background: '#fef3c7', color: '#b45309', padding: '0.6rem', borderRadius: '8px', textAlign: 'center', marginBottom: '1rem', fontWeight: 600, fontSize: '0.9rem', border: '1px solid #fcd34d', boxShadow: '0 0 15px rgba(245, 158, 11, 0.2)'}}>
          🔥 ALERTA ATHENA: Gol Inminente Detectado (Presión Extrema - Alta Probabilidad de Próximo Gol)
        </div>
      )}

      {athenaData && (
        <div className="athena-panel">
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
              <span style={{fontSize: '1.5rem'}}>🦉</span>
              <h3 style={{margin: 0, color: '#f8fafc', letterSpacing: '1px'}}>ATHENA LIVE ENGINE v1.1</h3>
            </div>
            <div style={{background: athenaData.state === 'BET' ? '#10b981' : athenaData.state === 'WATCH' ? '#f59e0b' : athenaData.state === 'VALUE CANDIDATE' ? '#8b5cf6' : '#334155', padding: '0.4rem 1rem', borderRadius: '20px', fontWeight: 800, fontSize: '0.8rem', color: 'white', letterSpacing: '1px', boxShadow: '0 0 10px rgba(0,0,0,0.5)'}}>
              ESTADO: {athenaData.state}
            </div>
          </div>
          
          <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginTop: '1.5rem'}}>
            <div className="athena-stat-box">
              <div style={{color: '#94a3b8', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '1px'}}>GOAL PRESSURE INDEX (GPI)</div>
              <div style={{fontSize: '2.5rem', fontWeight: 900, color: athenaData.gpi >= 60 ? '#ef4444' : '#38bdf8', marginTop: '0.5rem', textShadow: athenaData.gpi >= 60 ? '0 0 15px rgba(239, 68, 68, 0.4)' : 'none'}}>{athenaData.gpi}</div>
              <div style={{fontSize: '0.75rem', color: '#cbd5e1'}}>Presión: {athenaData.reading}</div>
            </div>
            <div className="athena-stat-box">
              <div style={{color: '#94a3b8', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '1px'}}>MOMENTUM (Δ)</div>
              <div style={{fontSize: '2.5rem', fontWeight: 900, color: athenaData.momentum > 0 ? '#10b981' : '#ef4444', marginTop: '0.5rem', textShadow: athenaData.momentum > 0 ? '0 0 15px rgba(16, 185, 129, 0.4)' : 'none'}}>{athenaData.momentum > 0 ? '+' : ''}{athenaData.momentum}</div>
              <div style={{fontSize: '0.75rem', color: '#cbd5e1'}}>Aceleración de Ataque</div>
            </div>
            <div className="athena-stat-box">
              <div style={{color: '#94a3b8', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '1px'}}>RECOMENDACIÓN OVER 0.5 HT</div>
              <div style={{fontSize: '1.2rem', fontWeight: 900, color: athenaData.state === 'BET' ? '#10b981' : '#94a3b8', marginTop: '1rem'}}>
                {athenaData.state === 'BET' ? '🔥 ALERTA DE GOL' : 'ESPERAR'}
              </div>
            </div>
          </div>
           <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginTop: '1rem'}}>
        
        <div style={{background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '16px', padding: '1.5rem', boxShadow: 'inset 0 0 20px rgba(16, 185, 129, 0.02)'}}>
          <div style={{color: '#10b981', fontWeight: 800, fontSize: '0.85rem', letterSpacing: '1px', marginBottom: '1rem'}}>🟢 MAIN LINE (SEGURA)</div>
          {match.analysis?.main_line ? (
            <div>
              <div style={{fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc'}}>{match.analysis.main_line.pick}</div>
              <div style={{display: 'flex', flexDirection: 'column', marginTop: '0.8rem', gap: '0.2rem'}}>
                <span style={{color: '#94a3b8', fontSize: '0.9rem', fontWeight: 500}}>Índice AVI: <span style={{color: '#10b981', fontWeight: 700}}>+{match.analysis.main_line.edge}%</span></span>
                <span style={{color: '#94a3b8', fontSize: '0.9rem', fontWeight: 500}}>Inversión: <span style={{color: '#f8fafc', fontWeight: 700}}>{match.analysis.main_line.kelly_percent}% Bank</span></span>
                {match.analysis.main_line.bookmaker && (
                  <span style={{color: '#94a3b8', fontSize: '0.85rem', fontWeight: 500, marginTop: '0.2rem'}}>Bookie: <span style={{color: '#f8fafc'}}>{match.analysis.main_line.bookmaker}</span></span>
                )}
              </div>
              <button 
                onClick={() => onPlaceBet(match.id, `${match.homeTeam} vs ${match.awayTeam}: ${match.analysis.main_line?.pick}`, match.analysis.main_line?.odds, match.analysis.main_line?.kelly_percent, match.status === 'LIVE' ? 'LIVE' : 'PRE')}
                style={{marginTop: '1rem', width: '100%', padding: '0.6rem', background: '#10b981', color: '#111827', border: 'none', borderRadius: '6px', fontWeight: 800, cursor: 'pointer', transition: '0.2s', boxShadow: '0 0 10px rgba(16, 185, 129, 0.3)'}}
              >
                + Rastrear Apuesta
              </button>
            </div>
          ) : (
            <div style={{color: '#475569', fontStyle: 'italic', fontSize: '0.9rem', marginTop: '1rem', fontWeight: 500}}>Sin línea segura.</div>
          )}
        </div>

        <div style={{background: 'rgba(245, 158, 11, 0.05)', border: '1px solid rgba(245, 158, 11, 0.2)', borderRadius: '16px', padding: '1.5rem', boxShadow: 'inset 0 0 20px rgba(245, 158, 11, 0.02)'}}>
          <div style={{color: '#f59e0b', fontWeight: 800, fontSize: '0.85rem', letterSpacing: '1px', marginBottom: '1rem'}}>🟡 LÍNEA DE VALOR (AVI)</div>
          {match.analysis?.medium_risk ? (
            <div>
              <div style={{fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc'}}>{match.analysis.medium_risk.pick}</div>
              <div style={{display: 'flex', flexDirection: 'column', marginTop: '0.8rem', gap: '0.2rem'}}>
                <span style={{color: '#94a3b8', fontSize: '0.9rem', fontWeight: 500}}>Índice AVI: <span style={{color: '#f59e0b', fontWeight: 700}}>+{match.analysis.medium_risk.edge}%</span></span>
                <span style={{color: '#94a3b8', fontSize: '0.9rem', fontWeight: 500}}>Inversión: <span style={{color: '#f8fafc', fontWeight: 700}}>{match.analysis.medium_risk.kelly_percent}% Bank</span></span>
                {match.analysis.medium_risk.bookmaker && (
                  <span style={{color: '#94a3b8', fontSize: '0.85rem', fontWeight: 500, marginTop: '0.2rem'}}>Bookie: <span style={{color: '#f8fafc'}}>{match.analysis.medium_risk.bookmaker}</span></span>
                )}
              </div>
              <button 
                onClick={() => onPlaceBet(match.id, `${match.homeTeam} vs ${match.awayTeam}: ${match.analysis.medium_risk?.pick}`, match.analysis.medium_risk?.odds, match.analysis.medium_risk?.kelly_percent, match.status === 'LIVE' ? 'LIVE' : 'PRE')}
                style={{marginTop: '1rem', width: '100%', padding: '0.6rem', background: '#f59e0b', color: '#111827', border: 'none', borderRadius: '6px', fontWeight: 800, cursor: 'pointer', transition: '0.2s', boxShadow: '0 0 10px rgba(245, 158, 11, 0.3)'}}
              >
                + Rastrear Apuesta
              </button>
            </div>
          ) : (
            <div style={{color: '#475569', fontStyle: 'italic', fontSize: '0.9rem', marginTop: '1rem', fontWeight: 500}}>Sin valor detectado.</div>
          )}
        </div>

              </div>
      </div>
      )}

    </div>
  );
}

const MatchDashboard = ({ cMatch, onBack }: { cMatch: any, onBack: () => void }) => {
  const [loadingInsights, setLoadingInsights] = useState(true);
  const [insights, setInsights] = useState<any>(null);
  
  // Manual Odds State (Persistent per match)
  const [oddsHome, setOddsHome] = useState(() => localStorage.getItem(`odds_home_${cMatch.id}`) || '');
  const [oddsDraw, setOddsDraw] = useState(() => localStorage.getItem(`odds_draw_${cMatch.id}`) || '');
  const [oddsAway, setOddsAway] = useState(() => localStorage.getItem(`odds_away_${cMatch.id}`) || '');
  const [oddsDc1x, setOddsDc1x] = useState(() => localStorage.getItem(`odds_dc1x_${cMatch.id}`) || '');
  const [oddsDcX2, setOddsDcX2] = useState(() => localStorage.getItem(`odds_dcx2_${cMatch.id}`) || '');
  const [oddsDc12, setOddsDc12] = useState(() => localStorage.getItem(`odds_dc12_${cMatch.id}`) || '');
  const [oddsDnbHome, setOddsDnbHome] = useState(() => localStorage.getItem(`odds_dnbh_${cMatch.id}`) || '');
  const [oddsDnbAway, setOddsDnbAway] = useState(() => localStorage.getItem(`odds_dnba_${cMatch.id}`) || '');
  const [oddsOver15, setOddsOver15] = useState(() => localStorage.getItem(`odds_o15_${cMatch.id}`) || '');
  const [oddsUnder15, setOddsUnder15] = useState(() => localStorage.getItem(`odds_u15_${cMatch.id}`) || '');
  const [oddsOver25, setOddsOver25] = useState(() => localStorage.getItem(`odds_o25_${cMatch.id}`) || '');
  const [oddsUnder25, setOddsUnder25] = useState(() => localStorage.getItem(`odds_u25_${cMatch.id}`) || '');
  const [oddsBttsYes, setOddsBttsYes] = useState(() => localStorage.getItem(`odds_byes_${cMatch.id}`) || '');
  const [oddsBttsNo, setOddsBttsNo] = useState(() => localStorage.getItem(`odds_bno_${cMatch.id}`) || '');
  const [oddsExactScore, setOddsExactScore] = useState(() => localStorage.getItem(`odds_exact_${cMatch.id}`) || '');
  const [stakeAmount, setStakeAmount] = useState('');
  const [realOdds, setRealOdds] = useState('');
  const [selectedBetType, setSelectedBetType] = useState('value_pick');

  // ARES State (Live Calculator)
  const [aresMinute, setAresMinute] = useState('70');
  const [aresHomeGoals, setAresHomeGoals] = useState('0');
  const [aresAwayGoals, setAresAwayGoals] = useState('0');
  const [aresCurrentCorners, setAresCurrentCorners] = useState('0');
  const [aresMarket, setAresMarket] = useState('over_0_5');
  const [aresOdds, setAresOdds] = useState('');
  const [aresResult, setAresResult] = useState<any>(null);
  const [aresLoading, setAresLoading] = useState(false);

  // Save to local storage on change
  useEffect(() => {
    localStorage.setItem(`odds_home_${cMatch.id}`, oddsHome);
    localStorage.setItem(`odds_draw_${cMatch.id}`, oddsDraw);
    localStorage.setItem(`odds_away_${cMatch.id}`, oddsAway);
    localStorage.setItem(`odds_dc1x_${cMatch.id}`, oddsDc1x);
    localStorage.setItem(`odds_dcx2_${cMatch.id}`, oddsDcX2);
    localStorage.setItem(`odds_dc12_${cMatch.id}`, oddsDc12);
    localStorage.setItem(`odds_dnbh_${cMatch.id}`, oddsDnbHome);
    localStorage.setItem(`odds_dnba_${cMatch.id}`, oddsDnbAway);
    localStorage.setItem(`odds_o15_${cMatch.id}`, oddsOver15);
    localStorage.setItem(`odds_u15_${cMatch.id}`, oddsUnder15);
    localStorage.setItem(`odds_o25_${cMatch.id}`, oddsOver25);
    localStorage.setItem(`odds_u25_${cMatch.id}`, oddsUnder25);
    localStorage.setItem(`odds_byes_${cMatch.id}`, oddsBttsYes);
    localStorage.setItem(`odds_bno_${cMatch.id}`, oddsBttsNo);
    localStorage.setItem(`odds_exact_${cMatch.id}`, oddsExactScore);
  }, [oddsHome, oddsDraw, oddsAway, oddsDc1x, oddsDcX2, oddsDc12, oddsDnbHome, oddsDnbAway, oddsOver15, oddsUnder15, oddsOver25, oddsUnder25, oddsBttsYes, oddsBttsNo, oddsExactScore, cMatch.id]);

  useEffect(() => {
    if (insights?.hermes?.recommended_units !== undefined) {
      setStakeAmount((insights.hermes.recommended_units * 100).toString());
    }
  }, [insights?.hermes?.recommended_units]);

  useEffect(() => {
    const fetchInsights = async () => {
      setLoadingInsights(true);
      try {
        const res = await fetch(`${API_BASE}/api/prematch-insight`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({homeTeam: cMatch.homeTeam, awayTeam: cMatch.awayTeam, match_id: String(cMatch.id)})
        });
        const data = await res.json();
        setInsights(data.probs);
      } catch (e) {
        console.error(e);
      }
      setLoadingInsights(false);
    };
    fetchInsights();
  }, [cMatch]);

  const calculateEdge = (probPercent: number, oddsStr: string) => {
    const odds = parseFloat(oddsStr);
    if (isNaN(odds) || odds <= 1.0) return null;
    const prob = probPercent / 100.0;
    const edge = (prob * odds) - 1;
    return (edge * 100).toFixed(2);
  };

  const handleRecalculateHermes = async () => {
    try {
      const odds = {
        home: oddsHome, draw: oddsDraw, away: oddsAway,
        dc_1x: oddsDc1x, dc_x2: oddsDcX2, dc_12: oddsDc12,
        dnb_home: oddsDnbHome, dnb_away: oddsDnbAway,
        over_1_5: oddsOver15, under_1_5: oddsUnder15,
        over_2_5: oddsOver25, under_2_5: oddsUnder25,
        btts_yes: oddsBttsYes, btts_no: oddsBttsNo
      };
      
      const res = await fetch(`${API_BASE}/api/recalculate-hermes`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          homeTeam: cMatch.homeTeam,
          awayTeam: cMatch.awayTeam,
          home_xg: insights.metrics.home_xg,
          away_xg: insights.metrics.away_xg,
          odds: odds,
          probs: insights,
          home_injuries: insights.context?.home_injuries || 0,
          away_injuries: insights.context?.away_injuries || 0,
          home_red_cards: insights.context?.home_red_cards || 0,
          away_red_cards: insights.context?.away_red_cards || 0
        })
      });
      const data = await res.json();
      setInsights((prev: any) => ({ ...prev, hermes: data.hermes }));
    } catch (e) {
      console.error(e);
    }
  };

  const handleAresCalculate = async () => {
    if (!aresOdds || isNaN(parseFloat(aresOdds))) { alert("Ingresa una cuota válida para ARES"); return; }
    setAresLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/ares/calculate`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          homeTeam: cMatch.homeTeam,
          awayTeam: cMatch.awayTeam,
          minute: parseInt(aresMinute),
          homeGoals: parseInt(aresHomeGoals),
          awayGoals: parseInt(aresAwayGoals),
          market: aresMarket,
          odds: parseFloat(aresOdds),
          currentCorners: parseInt(aresCurrentCorners) || 0
        })
      });
      const data = await res.json();
      setAresResult(data);
    } catch (e) {
      console.error(e);
    }
    setAresLoading(false);
  };

  const handleExecuteBet = async () => {
    if (!stakeAmount || parseFloat(stakeAmount) <= 0) {
      alert("Por favor ingresa un monto válido (Stake).");
      return;
    }
    if (!realOdds || parseFloat(realOdds) <= 1.0) {
      alert("Por favor ingresa la cuota real con la que tomaste la apuesta.");
      return;
    }
    
    // Si es un NO BET no dejamos apostar
    if (insights.hermes.pick.includes("NO BET")) {
      alert("No puedes registrar un NO BET. El algoritmo indica que no hay valor matemático.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/portfolio/bet`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          match_id: String(cMatch.id),
          pick: `${cMatch.homeTeam} vs ${cMatch.awayTeam}: ${insights.hermes[selectedBetType]}`,
          odds: parseFloat(realOdds),
          stake: parseFloat(stakeAmount),
          evidence_snapshot: JSON.stringify(insights)
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        alert(`¡Inversión registrada en Ledger! Nuevo Bankroll: $${data.new_bankroll.toFixed(2)}`);
        setRealOdds(''); // Clear input
      } else {
        alert(`Error: ${data.message}`);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const renderEdgeBadge = (prob: number, oddsStr: string) => {
    const edge = calculateEdge(prob, oddsStr);
    if (edge === null) return null;
    const edgeVal = parseFloat(edge);
    if (edgeVal > 0) {
      return <span style={{background: '#10b981', color: '#111827', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 800}}>AVI +{edge}% ✅</span>;
    } else {
      return <span style={{background: '#ef4444', color: 'white', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 800}}>AVI {edge}% ❌</span>;
    }
  };

  if (loadingInsights) {
    return (
      <div className="loader-container">
        <div className="spinner"></div>
        <p style={{ color: "var(--text-muted)", fontWeight: 600 }}>Cargando ATHENA Engine para {cMatch.homeTeam} vs {cMatch.awayTeam}...</p>
      </div>
    );
  }

  return (
    <div style={{animation: 'fadeIn 0.3s ease-out'}}>
      {/* Botón Volver */}
      <button 
        onClick={onBack}
        style={{background: 'rgba(255,255,255,0.05)', color: '#cbd5e1', border: '1px solid rgba(255,255,255,0.1)', padding: '0.6rem 1.2rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', transition: '0.2s'}}
        onMouseOver={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; e.currentTarget.style.color = '#f8fafc'; }}
        onMouseOut={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; e.currentTarget.style.color = '#cbd5e1'; }}
      >
        <span>⬅️</span> Volver al Calendario
      </button>

      {/* Header Dashboard */}
      <div style={{background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9))', border: '1px solid #334155', borderRadius: '16px', padding: '2rem', marginBottom: '2rem', display: 'flex', flexWrap: 'wrap', gap: '1.5rem', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 10px 30px -10px rgba(0,0,0,0.5)'}}>
        <div>
          <div style={{color: '#38bdf8', fontWeight: 800, fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem'}}>{cMatch.league} • {cMatch.round} • {cMatch.startTime}</div>
          <div style={{display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.5rem', fontSize: '1.6rem', fontWeight: 900, color: '#f8fafc'}}>
            <span>{cMatch.homeTeam}</span>
            <span style={{color: '#475569', fontSize: '1.2rem', fontWeight: 700}}>VS</span>
            <span>{cMatch.awayTeam}</span>
            {insights?.context && (
                <div style={{display: 'flex', gap: '1rem', marginTop: '1rem', flexWrap: 'wrap'}}>
                    {(insights.context.home_injuries > 0 || insights.context.home_red_cards > 0) && (
                        <div style={{display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '0.3rem 0.6rem', borderRadius: '4px'}}>
                            <span style={{fontSize: '0.75rem', color: '#fca5a5', fontWeight: 'bold'}}>{cMatch.homeTeam}:</span>
                            {insights.context.home_injuries > 0 && <span style={{fontSize: '0.75rem', color: '#ef4444'}}>🏥 {insights.context.home_injuries} Bajas</span>}
                            {insights.context.home_red_cards > 0 && <span style={{fontSize: '0.75rem', color: '#ef4444'}}>🟥 {insights.context.home_red_cards} Rojas(T)</span>}
                        </div>
                    )}
                    {(insights.context.away_injuries > 0 || insights.context.away_red_cards > 0) && (
                        <div style={{display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '0.3rem 0.6rem', borderRadius: '4px'}}>
                            <span style={{fontSize: '0.75rem', color: '#fca5a5', fontWeight: 'bold'}}>{cMatch.awayTeam}:</span>
                            {insights.context.away_injuries > 0 && <span style={{fontSize: '0.75rem', color: '#ef4444'}}>🏥 {insights.context.away_injuries} Bajas</span>}
                            {insights.context.away_red_cards > 0 && <span style={{fontSize: '0.75rem', color: '#ef4444'}}>🟥 {insights.context.away_red_cards} Rojas(T)</span>}
                        </div>
                    )}
                </div>
            )}
          </div>
        </div>
        <div style={{textAlign: 'right'}}>
          <div style={{background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', color: '#38bdf8', padding: '0.5rem 1rem', borderRadius: '8px', fontWeight: 800, fontSize: '0.9rem', display: 'inline-block'}}>
            🧠 ATHENA ENGINE ACTIVO
          </div>
          {insights?.is_ensembled && (
            <div style={{marginTop: '0.5rem', fontSize: '0.8rem', color: '#10b981', fontWeight: 700}}>Machine Learning Habilitado</div>
          )}
        </div>
      </div>

      {/* Grilla de Módulos */}
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))', gap: '1.5rem'}}>
        
        {/* Módulo 1X2 */}
        <div style={{background: 'rgba(15, 23, 42, 0.6)', border: '1px solid #334155', borderRadius: '16px', padding: '1.5rem'}}>
          <h3 style={{color: '#f8fafc', fontSize: '1.2rem', marginBottom: '1.5rem', borderBottom: '1px solid #334155', paddingBottom: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
            <span>⚖️</span> La Balanza de Temis (1X2)
          </h3>
          <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            {/* Local */}
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #10b981'}}>
              <div>
                <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Gana Local</div>
                <div style={{color: '#f8fafc', fontWeight: 800, fontSize: '1.2rem'}}>{insights.home.toFixed(1)}%</div>
              </div>
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem'}}>
                <input type="number" placeholder="Cuota" value={oddsHome} onChange={e => setOddsHome(e.target.value)} style={{width: '80px', padding: '0.5rem', borderRadius: '6px', background: '#1e293b', border: '1px solid #475569', color: 'white', textAlign: 'center', fontWeight: 700}} />
                {renderEdgeBadge(insights.home, oddsHome)}
              </div>
            </div>
            {/* Empate */}
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #f59e0b'}}>
              <div>
                <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Empate</div>
                <div style={{color: '#f8fafc', fontWeight: 800, fontSize: '1.2rem'}}>{insights.draw.toFixed(1)}%</div>
              </div>
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem'}}>
                <input type="number" placeholder="Cuota" value={oddsDraw} onChange={e => setOddsDraw(e.target.value)} style={{width: '80px', padding: '0.5rem', borderRadius: '6px', background: '#1e293b', border: '1px solid #475569', color: 'white', textAlign: 'center', fontWeight: 700}} />
                {renderEdgeBadge(insights.draw, oddsDraw)}
              </div>
            </div>
            {/* Visita */}
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #ef4444'}}>
              <div>
                <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Gana Visita</div>
                <div style={{color: '#f8fafc', fontWeight: 800, fontSize: '1.2rem'}}>{insights.away.toFixed(1)}%</div>
              </div>
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem'}}>
                <input type="number" placeholder="Cuota" value={oddsAway} onChange={e => setOddsAway(e.target.value)} style={{width: '80px', padding: '0.5rem', borderRadius: '6px', background: '#1e293b', border: '1px solid #475569', color: 'white', textAlign: 'center', fontWeight: 700}} />
                {renderEdgeBadge(insights.away, oddsAway)}
              </div>
            </div>
            
            {/* DOBLE OPORTUNIDAD Y DNB */}
            <h4 style={{fontSize: '1.2rem', color: '#e2e8f0', marginTop: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem', marginBottom: '1.5rem'}}>Mercados Seguros (Nuevos)</h4>
            <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
              {/* DOBLE OPORTUNIDAD 1X */}
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '12px'}}>
                <div>
                  <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Doble Oportunidad (1X)</div>
                  <div style={{fontSize: '1.1rem', fontWeight: 700}}>{cMatch.homeTeam} o Empate</div>
                  <div style={{color: '#f8fafc', fontSize: '0.9rem'}}>Probabilidad: <span style={{fontWeight: 700, color: '#10b981'}}>{insights.dc_1x?.toFixed(1)}%</span></div>
                </div>
                <input type="number" placeholder="Cuota" value={oddsDc1x} onChange={e => setOddsDc1x(e.target.value)} style={{width: '80px', padding: '0.5rem', borderRadius: '6px', background: '#1e293b', border: '1px solid #475569', color: 'white', textAlign: 'center', fontWeight: 700}} />
              </div>
              
              {/* DOBLE OPORTUNIDAD X2 */}
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '12px'}}>
                <div>
                  <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Doble Oportunidad (X2)</div>
                  <div style={{fontSize: '1.1rem', fontWeight: 700}}>{cMatch.awayTeam} o Empate</div>
                  <div style={{color: '#f8fafc', fontSize: '0.9rem'}}>Probabilidad: <span style={{fontWeight: 700, color: '#10b981'}}>{insights.dc_x2?.toFixed(1)}%</span></div>
                </div>
                <input type="number" placeholder="Cuota" value={oddsDcX2} onChange={e => setOddsDcX2(e.target.value)} style={{width: '80px', padding: '0.5rem', borderRadius: '6px', background: '#1e293b', border: '1px solid #475569', color: 'white', textAlign: 'center', fontWeight: 700}} />
              </div>
              
              {/* DNB HOME */}
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '12px'}}>
                <div>
                  <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Empate No Acción (DNB)</div>
                  <div style={{fontSize: '1.1rem', fontWeight: 700}}>{cMatch.homeTeam}</div>
                  <div style={{color: '#f8fafc', fontSize: '0.9rem'}}>Probabilidad (Excluyendo Empate): <span style={{fontWeight: 700, color: '#38bdf8'}}>{insights.dnb_home?.toFixed(1)}%</span></div>
                </div>
                <input type="number" placeholder="Cuota" value={oddsDnbHome} onChange={e => setOddsDnbHome(e.target.value)} style={{width: '80px', padding: '0.5rem', borderRadius: '6px', background: '#1e293b', border: '1px solid #475569', color: 'white', textAlign: 'center', fontWeight: 700}} />
              </div>
              
              {/* DNB AWAY */}
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '12px'}}>
                <div>
                  <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Empate No Acción (DNB)</div>
                  <div style={{fontSize: '1.1rem', fontWeight: 700}}>{cMatch.awayTeam}</div>
                  <div style={{color: '#f8fafc', fontSize: '0.9rem'}}>Probabilidad (Excluyendo Empate): <span style={{fontWeight: 700, color: '#38bdf8'}}>{insights.dnb_away?.toFixed(1)}%</span></div>
                </div>
                <input type="number" placeholder="Cuota" value={oddsDnbAway} onChange={e => setOddsDnbAway(e.target.value)} style={{width: '80px', padding: '0.5rem', borderRadius: '6px', background: '#1e293b', border: '1px solid #475569', color: 'white', textAlign: 'center', fontWeight: 700}} />
              </div>
            </div>
          </div>
        </div>

        {/* Módulo ARES (Calculadora En Vivo) */}
        <div style={{background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: '16px', padding: '1.5rem', marginBottom: '2rem', boxShadow: '0 0 20px rgba(239, 68, 68, 0.1)'}}>
          <h3 style={{color: '#fca5a5', fontSize: '1.4rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 900}}>
            <span>⚔️</span> ARES: Calculadora Táctica En Vivo
          </h3>
          
          <div style={{display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.5rem'}}>
            <div style={{flex: 1, minWidth: '100px'}}>
              <label style={{display: 'block', color: '#94a3b8', fontSize: '0.85rem', marginBottom: '0.5rem'}}>Minuto Actual</label>
              <input type="number" value={aresMinute} onChange={e => setAresMinute(e.target.value)} style={{width: '100%', padding: '0.8rem', borderRadius: '8px', background: '#1e293b', border: '1px solid #475569', color: 'white', fontWeight: 700}} />
            </div>
            <div style={{flex: 1, minWidth: '100px'}}>
              <label style={{display: 'block', color: '#94a3b8', fontSize: '0.85rem', marginBottom: '0.5rem'}}>Goles {cMatch.homeTeam}</label>
              <input type="number" value={aresHomeGoals} onChange={e => setAresHomeGoals(e.target.value)} style={{width: '100%', padding: '0.8rem', borderRadius: '8px', background: '#1e293b', border: '1px solid #475569', color: 'white', fontWeight: 700}} />
            </div>
            <div style={{flex: 1, minWidth: '100px'}}>
              <label style={{display: 'block', color: '#94a3b8', fontSize: '0.85rem', marginBottom: '0.5rem'}}>Goles {cMatch.awayTeam}</label>
              <input type="number" value={aresAwayGoals} onChange={e => setAresAwayGoals(e.target.value)} style={{width: '100%', padding: '0.8rem', borderRadius: '8px', background: '#1e293b', border: '1px solid #475569', color: 'white', fontWeight: 700}} />
            </div>
            {aresMarket.includes('corners') && (
              <div style={{flex: 1, minWidth: '100px'}}>
                <label style={{display: 'block', color: '#94a3b8', fontSize: '0.85rem', marginBottom: '0.5rem'}}>Corners Actuales</label>
                <input type="number" value={aresCurrentCorners} onChange={e => setAresCurrentCorners(e.target.value)} style={{width: '100%', padding: '0.8rem', borderRadius: '8px', background: '#1e293b', border: '1px solid #f59e0b', color: 'white', fontWeight: 700}} />
              </div>
            )}
          </div>
          
          <div style={{display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end'}}>
            <div style={{flex: 2, minWidth: '200px'}}>
              <label style={{display: 'block', color: '#94a3b8', fontSize: '0.85rem', marginBottom: '0.5rem'}}>Mercado (Casino)</label>
              <select value={aresMarket} onChange={e => setAresMarket(e.target.value)} style={{width: '100%', padding: '0.8rem', borderRadius: '8px', background: '#1e293b', border: '1px solid #475569', color: 'white', fontWeight: 700, appearance: 'none'}}>
                <option value="home">Gana Local</option>
                <option value="draw">Empate</option>
                <option value="away">Gana Visita</option>
                <option value="over_0_5">Más 0.5 Goles</option>
                <option value="under_0_5">Menos 0.5 Goles</option>
                <option value="over_1_5">Más 1.5 Goles</option>
                <option value="over_2_5">Más 2.5 Goles</option>
                <option value="over_0_5_ht">Más 0.5 Goles (1er Tiempo)</option>
                <option value="over_1_5_ht">Más 1.5 Goles (1er Tiempo)</option>
                <option value="btts_yes">Ambos Anotan (SÍ)</option>
                <option value="btts_no">Ambos Anotan (NO)</option>
                <option value="over_8_5_corners">Más 8.5 Corners Totales</option>
                <option value="over_9_5_corners">Más 9.5 Corners Totales</option>
                <option value="over_10_5_corners">Más 10.5 Corners Totales</option>
              </select>
            </div>
            <div style={{flex: 1, minWidth: '100px'}}>
              <label style={{display: 'block', color: '#94a3b8', fontSize: '0.85rem', marginBottom: '0.5rem'}}>Cuota</label>
              <input type="number" step="0.01" value={aresOdds} onChange={e => setAresOdds(e.target.value)} placeholder="Ej. 1.85" style={{width: '100%', padding: '0.8rem', borderRadius: '8px', background: '#1e293b', border: '1px solid #ef4444', color: 'white', fontWeight: 700}} />
            </div>
            <button 
              onClick={handleAresCalculate} 
              disabled={aresLoading}
              style={{padding: '0.8rem 1.5rem', background: '#ef4444', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 800, cursor: 'pointer', flexShrink: 0}}
            >
              {aresLoading ? 'Calculando...' : '⚡ Disparar ARES'}
            </button>
          </div>
          
          {aresResult && (
            <div style={{marginTop: '1.5rem', padding: '1.5rem', background: 'rgba(0,0,0,0.4)', borderRadius: '12px', border: '1px solid #334155'}}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <div>
                  <div style={{color: '#94a3b8', fontSize: '0.9rem'}}>Probabilidad Real</div>
                  <div style={{color: '#f8fafc', fontSize: '2rem', fontWeight: 900}}>{aresResult.prob}%</div>
                </div>
                <div style={{textAlign: 'center'}}>
                  <div style={{color: '#94a3b8', fontSize: '0.9rem'}}>Cuota Casino</div>
                  <div style={{color: '#f8fafc', fontSize: '1.5rem', fontWeight: 700}}>{aresResult.odds}</div>
                </div>
                <div style={{textAlign: 'right'}}>
                  <div style={{color: '#94a3b8', fontSize: '0.9rem'}}>Valor Matemático (Edge)</div>
                  <div style={{
                    color: aresResult.edge > 0 ? '#10b981' : '#ef4444', 
                    fontSize: '2rem', 
                    fontWeight: 900,
                    textShadow: aresResult.edge > 0 ? '0 0 15px rgba(16, 185, 129, 0.4)' : 'none'
                  }}>
                    {aresResult.edge > 0 ? '+' : ''}{aresResult.edge}%
                  </div>
                </div>
              </div>
              {aresResult.edge > 5 && (
                <div style={{marginTop: '1rem', padding: '0.8rem', background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', borderRadius: '8px', fontWeight: 800, textAlign: 'center'}}>
                  🔥 ¡ALERTA DE VALUE BET! DISPARA AHORA 🔥
                </div>
              )}
            </div>
          )}
        </div>

        {/* Módulo Goles */}
        <div style={{background: 'rgba(15, 23, 42, 0.6)', border: '1px solid #334155', borderRadius: '16px', padding: '1.5rem'}}>
          <h3 style={{color: '#f8fafc', fontSize: '1.2rem', marginBottom: '1.5rem', borderBottom: '1px solid #334155', paddingBottom: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
            <span>🔥</span> La Furia de Ares (Goles)
          </h3>
          
          {/* MERCADO DE GOLES */}
          <h4 style={{fontSize: '1.2rem', color: '#e2e8f0', marginTop: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem', marginBottom: '1.5rem'}}>Mercado de Goles Totales</h4>
          <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            
            {/* OVER 1.5 */}
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '12px'}}>
              <div>
                <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>OVER 1.5 GOLES</div>
                <div style={{fontSize: '1.1rem', fontWeight: 700}}>Más de 1.5 Goles</div>
                <div style={{color: '#f8fafc', fontSize: '0.9rem'}}>Probabilidad Poisson: <span style={{fontWeight: 700, color: '#10b981'}}>{insights.over_1_5?.toFixed(1)}%</span></div>
              </div>
              <input type="number" placeholder="Cuota" value={oddsOver15} onChange={e => setOddsOver15(e.target.value)} style={{width: '80px', padding: '0.5rem', borderRadius: '6px', background: '#1e293b', border: '1px solid #475569', color: 'white', textAlign: 'center', fontWeight: 700}} />
            </div>

            {/* Over 2.5 */}
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #8b5cf6'}}>
              <div>
                <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Más de 2.5 Goles</div>
                <div style={{color: '#f8fafc', fontWeight: 800, fontSize: '1.2rem'}}>{insights.over_2_5.toFixed(1)}%</div>
              </div>
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem'}}>
                <input type="number" placeholder="Cuota" value={oddsOver25} onChange={e => setOddsOver25(e.target.value)} style={{width: '80px', padding: '0.5rem', borderRadius: '6px', background: '#1e293b', border: '1px solid #475569', color: 'white', textAlign: 'center', fontWeight: 700}} />
                {renderEdgeBadge(insights.over_2_5, oddsOver25)}
              </div>
            </div>
            {/* Under 2.5 — SHADOW MODE */}
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.15)', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #ef4444', boxShadow: '0 0 8px 2px rgba(239,68,68,0.45)', opacity: 0.8}}>
              <div>
                <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem'}}>
                  <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Menos de 2.5 Goles</div>
                  <div style={{background: '#374151', color: '#9ca3af', fontSize: '0.65rem', fontWeight: 800, padding: '0.15rem 0.5rem', borderRadius: '4px', border: '1px solid #ef4444', textTransform: 'uppercase', letterSpacing: '0.5px', boxShadow: '0 0 4px rgba(239,68,68,0.5)'}}>🔬 EN MONITOREO</div>
                </div>
                <div style={{color: '#f8fafc', fontWeight: 800, fontSize: '1.2rem'}}>{insights.under_2_5.toFixed(1)}%</div>
                <div style={{color: '#6b7280', fontSize: '0.7rem', marginTop: '0.2rem'}}>Sin recomendación — Acumulando datos con API PRO 2026</div>
              </div>
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem'}}>
                <input type="number" placeholder="Cuota" value={oddsUnder25} onChange={e => setOddsUnder25(e.target.value)} style={{width: '80px', padding: '0.5rem', borderRadius: '6px', background: '#111827', border: '1px solid #374151', color: '#6b7280', textAlign: 'center', fontWeight: 700}} />
              </div>
            </div>

            <div style={{height: '1px', background: '#334155', margin: '0.5rem 0'}}></div>

            {/* BTTS Yes — SHADOW MODE */}
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.15)', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #ef4444', boxShadow: '0 0 8px 2px rgba(239,68,68,0.45)', opacity: 0.8}}>
              <div>
                <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem'}}>
                  <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Ambos Anotan (SÍ)</div>
                  <div style={{background: '#374151', color: '#9ca3af', fontSize: '0.65rem', fontWeight: 800, padding: '0.15rem 0.5rem', borderRadius: '4px', border: '1px solid #ef4444', textTransform: 'uppercase', letterSpacing: '0.5px', boxShadow: '0 0 4px rgba(239,68,68,0.5)'}}>🔬 EN MONITOREO</div>
                </div>
                <div style={{color: '#f8fafc', fontWeight: 800, fontSize: '1.2rem'}}>{insights.btts_yes.toFixed(1)}%</div>
                <div style={{color: '#6b7280', fontSize: '0.7rem', marginTop: '0.2rem'}}>Sin recomendación — Acumulando datos con API PRO 2026</div>
              </div>
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem'}}>
                <input type="number" placeholder="Cuota" value={oddsBttsYes} onChange={e => setOddsBttsYes(e.target.value)} style={{width: '80px', padding: '0.5rem', borderRadius: '6px', background: '#111827', border: '1px solid #374151', color: '#6b7280', textAlign: 'center', fontWeight: 700}} />
              </div>
            </div>

            {/* BTTS No — SHADOW MODE */}
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.15)', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #ef4444', boxShadow: '0 0 8px 2px rgba(239,68,68,0.45)', opacity: 0.8}}>
              <div>
                <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem'}}>
                  <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Ambos Anotan (NO)</div>
                  <div style={{background: '#374151', color: '#9ca3af', fontSize: '0.65rem', fontWeight: 800, padding: '0.15rem 0.5rem', borderRadius: '4px', border: '1px solid #ef4444', textTransform: 'uppercase', letterSpacing: '0.5px', boxShadow: '0 0 4px rgba(239,68,68,0.5)'}}>🔬 EN MONITOREO</div>
                </div>
                <div style={{color: '#f8fafc', fontWeight: 800, fontSize: '1.2rem'}}>{insights.btts_no.toFixed(1)}%</div>
                <div style={{color: '#6b7280', fontSize: '0.7rem', marginTop: '0.2rem'}}>Sin recomendación — Acumulando datos con API PRO 2026</div>
              </div>
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem'}}>
                <input type="number" placeholder="Cuota" value={oddsBttsNo} onChange={e => setOddsBttsNo(e.target.value)} style={{width: '80px', padding: '0.5rem', borderRadius: '6px', background: '#111827', border: '1px solid #374151', color: '#6b7280', textAlign: 'center', fontWeight: 700}} />
              </div>
            </div>
          </div>
        </div>

        {/* Módulo Especial & xG */}
        <div style={{background: 'rgba(15, 23, 42, 0.6)', border: '1px solid #334155', borderRadius: '16px', padding: '1.5rem'}}>
          <h3 style={{color: '#f8fafc', fontSize: '1.2rem', marginBottom: '1.5rem', borderBottom: '1px solid #334155', paddingBottom: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
            <span>🦉</span> La Sabiduría de Atenea (Avanzados)
          </h3>
          
          {/* xG */}
          <div style={{background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', marginBottom: '1rem'}}>
            <div style={{color: '#94a3b8', fontSize: '0.85rem', marginBottom: '0.5rem'}}>Goles Esperados (xG)</div>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <div style={{textAlign: 'center'}}>
                <div style={{color: '#38bdf8', fontWeight: 800, fontSize: '1.2rem'}}>{insights.metrics.home_xg.toFixed(2)}</div>
                <div style={{color: '#64748b', fontSize: '0.7rem'}}>LOCAL</div>
              </div>
              <div style={{color: '#475569', fontWeight: 800}}>VS</div>
              <div style={{textAlign: 'center'}}>
                <div style={{color: '#38bdf8', fontWeight: 800, fontSize: '1.2rem'}}>{insights.metrics.away_xg.toFixed(2)}</div>
                <div style={{color: '#64748b', fontSize: '0.7rem'}}>VISITA</div>
              </div>
            </div>
          </div>

          {/* Marcador Exacto */}
          <div style={{background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', marginBottom: '1rem', borderLeft: '4px solid #eab308'}}>
            <div style={{color: '#94a3b8', fontSize: '0.85rem', marginBottom: '0.5rem'}}>Marcador MÁS Probable</div>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <div>
                <div style={{color: '#f8fafc', fontWeight: 900, fontSize: '1.5rem'}}>{insights.exact_score}</div>
                <div style={{color: '#eab308', fontWeight: 700, fontSize: '0.9rem'}}>{insights.exact_score_prob.toFixed(1)}% Probabilidad</div>
              </div>
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem'}}>
                <input type="number" placeholder="Cuota" value={oddsExactScore} onChange={e => setOddsExactScore(e.target.value)} style={{width: '80px', padding: '0.5rem', borderRadius: '6px', background: '#1e293b', border: '1px solid #475569', color: 'white', textAlign: 'center', fontWeight: 700}} />
                {renderEdgeBadge(insights.exact_score_prob, oddsExactScore)}
              </div>
            </div>
          </div>

          {/* Corners (si existen) */}
          {insights.corners && (
            <div style={{background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #ec4899'}}>
              <div style={{color: '#94a3b8', fontSize: '0.85rem', marginBottom: '0.5rem'}}>Tiros de Esquina Proyectados</div>
              <div style={{color: '#f8fafc', fontWeight: 800, fontSize: '1.2rem'}}>{insights.corners.expected_total} Totales</div>
              <div style={{display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem'}}>
                <div style={{color: '#ec4899', fontSize: '0.8rem'}}>Over 9.5: {insights.corners.over_9_5_prob}%</div>
                <div style={{color: '#64748b', fontSize: '0.8rem'}}>Under 9.5: {insights.corners.under_9_5_prob}%</div>
              </div>
            </div>
          )}
        </div>

        {/* Módulo Hermes (Rule Engine) */}
        {insights.hermes && (
          <div style={{background: 'rgba(15, 23, 42, 0.6)', border: '1px solid #38bdf8', borderRadius: '16px', padding: '1.5rem', gridColumn: '1 / -1'}}>
            <h3 style={{color: '#38bdf8', fontSize: '1.2rem', marginBottom: '1.5rem', borderBottom: '1px solid rgba(56, 189, 248, 0.3)', paddingBottom: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
              <span>⚖️</span> El Oráculo de Hermes
            </h3>
            
            <div style={{display: 'flex', flexWrap: 'wrap', gap: '2rem'}}>
              <div style={{flex: '1 1 350px', display: 'flex', flexDirection: 'column', gap: '1rem'}}>
                
                {/* 🎯 El Francotirador */}
                <div style={{background: 'rgba(0,0,0,0.4)', padding: '1.5rem', borderRadius: '12px', borderLeft: '4px solid #8b5cf6'}}>
                  <div style={{color: '#94a3b8', fontSize: '0.9rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem'}}>
                    <span>🎯</span> Francotirador (Valor Matemático / Simple)
                  </div>
                  <div style={{fontSize: '1.5rem', fontWeight: 900, color: '#f8fafc', marginBottom: '1rem', lineHeight: '1.2'}}>
                    {insights.hermes.value_pick || insights.hermes.pick}
                  </div>
                  
                  <div style={{color: '#94a3b8', fontSize: '0.8rem', marginBottom: '0.5rem'}}>Confianza de Reglas</div>
                  <div style={{width: '100%', background: '#1e293b', borderRadius: '8px', height: '10px', overflow: 'hidden'}}>
                    <div style={{width: `${insights.hermes.value_confidence || insights.hermes.confidence}%`, background: 'linear-gradient(90deg, #38bdf8, #8b5cf6)', height: '100%'}}></div>
                  </div>
                  <div style={{textAlign: 'right', color: '#f8fafc', fontWeight: 800, marginTop: '0.4rem', fontSize: '1rem'}}>{insights.hermes.value_confidence || insights.hermes.confidence}%</div>
                </div>

                {/* 🧱 El Ladrillo */}
                <div style={{background: 'rgba(16, 185, 129, 0.05)', padding: '1.5rem', borderRadius: '12px', borderLeft: '4px solid #10b981'}}>
                  <div style={{color: '#10b981', fontSize: '0.9rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem'}}>
                    <span>🧱</span> Ladrillo (Alta Probabilidad / Combinada)
                  </div>
                  <div style={{fontSize: '1.5rem', fontWeight: 900, color: '#10b981', marginBottom: '1rem', lineHeight: '1.2'}}>
                    {insights.hermes.safe_pick || 'Buscando Cuota Segura > 1.60...'}
                  </div>
                  
                  <div style={{color: '#10b981', opacity: 0.8, fontSize: '0.8rem', marginBottom: '0.5rem'}}>Probabilidad Real Base</div>
                  <div style={{width: '100%', background: '#1e293b', borderRadius: '8px', height: '10px', overflow: 'hidden'}}>
                    <div style={{width: `${insights.hermes.safe_confidence || 0}%`, background: '#10b981', height: '100%'}}></div>
                  </div>
                  <div style={{textAlign: 'right', color: '#10b981', fontWeight: 800, marginTop: '0.4rem', fontSize: '1rem'}}>{insights.hermes.safe_confidence || 0}%</div>
                </div>
                
                {/* Panel de Ejecución y Recalibración */}
                <div style={{background: 'rgba(0,0,0,0.4)', padding: '1.5rem', borderRadius: '12px'}}>
                  <button onClick={handleRecalculateHermes} className="cyber-button" style={{width: '100%'}}>
                    ⚡ Recalibrar Veredictos con Cuotas
                  </button>

                  <div style={{marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.1)'}}>
                    <div style={{display: 'flex', gap: '1rem', marginBottom: '0.5rem'}}>
                      <div style={{flex: 1}}><div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Inversión (Stake)</div></div>
                      <div style={{flex: 1}}><div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Cuota Real (Momio)</div></div>
                    </div>
                    <div style={{display: 'flex', gap: '1rem'}}>
                      <input 
                        type="number" 
                        value={stakeAmount} 
                        onChange={e => setStakeAmount(e.target.value)} 
                        placeholder="Ej: 100"
                        style={{flex: 1, padding: '0.8rem', borderRadius: '8px', background: '#0f172a', border: '1px solid #38bdf8', color: 'white', fontWeight: 800, fontSize: '1.2rem', textAlign: 'center'}}
                      />
                      <input 
                        type="number" 
                        value={realOdds} 
                        onChange={e => setRealOdds(e.target.value)} 
                        placeholder="Ej: 1.85"
                        style={{flex: 1, padding: '0.8rem', borderRadius: '8px', background: '#0f172a', border: '1px solid #10b981', color: 'white', fontWeight: 800, fontSize: '1.2rem', textAlign: 'center'}}
                      />
                    </div>
                    {insights.hermes.recommended_units !== undefined && (
                      <div style={{color: '#10b981', fontSize: '0.75rem', marginTop: '0.4rem', textAlign: 'left'}}>
                        Recomendación ATHENA (Francotirador): {insights.hermes.recommended_units} Unidades
                      </div>
                    )}
                    
                    <div style={{marginTop: '1.5rem', background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)'}}>
                      <div style={{color: '#94a3b8', fontSize: '0.85rem', marginBottom: '0.8rem'}}>Selecciona la apuesta a guardar:</div>
                      <div style={{display: 'flex', gap: '1.5rem', flexWrap: 'wrap'}}>
                        <label style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: selectedBetType === 'value_pick' ? '#8b5cf6' : '#94a3b8', cursor: 'pointer', fontWeight: selectedBetType === 'value_pick' ? 700 : 400}}>
                          <input 
                            type="radio" 
                            name="betType" 
                            value="value_pick" 
                            checked={selectedBetType === 'value_pick'} 
                            onChange={() => setSelectedBetType('value_pick')} 
                            style={{accentColor: '#8b5cf6', width: '1.2rem', height: '1.2rem'}}
                          />
                          🎯 Francotirador
                        </label>
                        <label style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: selectedBetType === 'safe_pick' ? '#10b981' : '#94a3b8', cursor: 'pointer', fontWeight: selectedBetType === 'safe_pick' ? 700 : 400}}>
                          <input 
                            type="radio" 
                            name="betType" 
                            value="safe_pick" 
                            checked={selectedBetType === 'safe_pick'} 
                            onChange={() => setSelectedBetType('safe_pick')} 
                            style={{accentColor: '#10b981', width: '1.2rem', height: '1.2rem'}}
                          />
                          🧱 Ladrillo
                        </label>
                      </div>
                    </div>
                    
                    <button 
                      onClick={handleExecuteBet}
                      style={{marginTop: '1rem', width: '100%', background: 'linear-gradient(90deg, #10b981, #059669)', color: 'white', border: 'none', padding: '1rem', borderRadius: '8px', fontWeight: 800, fontSize: '1rem', cursor: 'pointer', boxShadow: '0 4px 15px rgba(16, 185, 129, 0.3)', transition: '0.2s'}}
                      onMouseOver={e => e.currentTarget.style.transform = 'translateY(-2px)'}
                      onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}
                    >
                      💰 Ejecutar y Guardar en Ledger
                    </button>
                  </div>
                </div>
              </div>
              
              <div style={{flex: '2 1 400px'}}>
                <div style={{color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1rem'}}>Lógica (Reglas Activadas)</div>
                <div style={{display: 'flex', flexDirection: 'column', gap: '0.8rem'}}>
                  {insights.hermes.rules_evaluated.map((rule: any, i: number) => (
                    <div key={i} style={{background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', borderLeft: `3px solid ${rule.score > 5 ? '#8b5cf6' : '#334155'}`}}>
                      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'}}>
                        <div>
                          <div style={{color: '#f8fafc', fontWeight: 700, fontSize: '0.95rem'}}>{rule.rule}</div>
                          <div style={{color: '#cbd5e1', fontSize: '0.85rem', marginTop: '0.2rem'}}>{rule.message}</div>
                        </div>
                        {rule.winner && (
                          <div style={{background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700, whiteSpace: 'nowrap'}}>
                            + {rule.score} {rule.winner}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [pinInput, setPinInput] = useState('');
  
  useEffect(() => {
    if (localStorage.getItem('athena_pin') === '7777') {
      setIsAuthenticated(true);
    }
  }, []);

  const handlePinSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (pinInput === '7777') {
      localStorage.setItem('athena_pin', '7777');
      setIsAuthenticated(true);
    } else {
      alert('PIN Incorrecto');
      setPinInput('');
    }
  };

  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('portfolio'); // 'radar', 'portfolio', 'calendar', 'match-detail', 'lab'
  const [labData, setLabData] = useState<any>(null);
  const [labLoading, setLabLoading] = useState(false);
  const [delfosAuditData, setDelfosAuditData] = useState<any>(null);
  const [delfosDiagnostic, setDelfosDiagnostic] = useState<any>(null);
  const [showDiagnostic, setShowDiagnostic] = useState(false);
  const [delfosLoading, setDelfosLoading] = useState(false);
  
  const [selectedMatch, setSelectedMatch] = useState<any>(null);
  
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [calendarMatches, setCalendarMatches] = useState<any[]>([]);
  const [calendarLoading, setCalendarLoading] = useState(false);
  const [collapsedCountries, setCollapsedCountries] = useState<Record<string, boolean>>({});
  const [calendarDate, setCalendarDate] = useState(() => {
    const today = new Date();
    today.setHours(today.getHours() - 6);
    return today.toISOString().split('T')[0];
  });
  const [oracleInsights, setOracleInsights] = useState<any[]>([]);
  const [oracleLoading, setOracleLoading] = useState(false);
  
  const [editingBetId, setEditingBetId] = useState<string | null>(null);
  const [editOddsValue, setEditOddsValue] = useState<number>(0);
  const [autotuneReport, setAutotuneReport] = useState<any>(null);
  
  // Nuevo estado para ARGOS
  const [argosActive, setArgosActive] = useState<boolean>(false);

  const fetchMatches = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/matches`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setMatches(data);
      } else {
        console.error("API Error: no array returned", data);
        setMatches([]);
      }
    } catch (e) {
      console.error(e);
      setMatches([]);
    }
    setLoading(false);
  };

  const fetchPortfolio = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/portfolio`);
      const data = await res.json();
      setPortfolio(data);
    } catch (e) { console.error(e); }
  };

  const fetchLab = async () => {
    setLabLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/lab`);
      const data = await res.json();
      setLabData(data);
    } catch (e) { console.error(e); }
    setLabLoading(false);
  };

  const fetchDelfosAudit = async () => {
    setDelfosLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/delfos/historial`);
      const data = await res.json();
      setDelfosAuditData(data);
    } catch (e) { console.error(e); }
    setDelfosLoading(false);
  };
  
  const fetchArgosStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/argos/status`);
      const data = await res.json();
      setArgosActive(data.argos_active);
    } catch (e) { console.error(e); }
  };

  const toggleArgos = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/argos/toggle`, { method: 'POST' });
      const data = await res.json();
      setArgosActive(data.argos_active);
    } catch (e) { console.error(e); }
  };

  const handlePlaceBet = async (matchId: string, pick: string, odds: number, kellyPercent: number, betType: string = "PRE") => {
    if (!portfolio) return;
    let stake = portfolio.bankroll * ((kellyPercent || 0.1) / 100);
    if (isNaN(stake) || stake <= 0) stake = portfolio.bankroll * 0.01;
    stake = Math.round(stake * 100) / 100; // Round to 2 decimal places
    
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/bet`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ match_id: matchId, pick, odds, stake, bet_type: betType })
      });
      const data = await res.json();
      if (data.status === "success") {
        fetchPortfolio();
        alert(`✅ Apuesta colocada con éxito: $${stake.toFixed(2)} a ${pick}`);
      } else {
        alert("❌ Error: " + data.message);
      }
    } catch (e) { console.error(e); }
  };

  const handleSettleBet = async (betId: string, result: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/settle/${betId}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ result })
      });
      fetchPortfolio();
    } catch (e) { console.error(e); }
  };

  const handleDeleteBet = async (betId: string) => {
    if (!confirm("¿Estás seguro de que deseas eliminar esta entrada del Ledger? Esta acción revertirá el bankroll asociado.")) return;
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/bets/${betId}`, {
        method: "DELETE", headers: { "Content-Type": "application/json" }
      });
      fetchPortfolio();
    } catch (e) { console.error(e); }
  };

  const handleUpdateOdds = async (betId: string) => {
    if (!editOddsValue || isNaN(editOddsValue)) return;
    try {
      await fetch(`${API_BASE}/api/portfolio/bets/${betId}/odds`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ odds: editOddsValue })
      });
      setEditingBetId(null);
      fetchPortfolio();
    } catch (e) { console.error(e); }
  };

  const handleAutopsy = async () => {
    if (confirm("¿Ejecutar Autopsia de ATHENA? Esto buscará los marcadores finales reales de todas las apuestas ABIERTAS y actualizará tu capital.")) {
      try {
        const res = await fetch(`${API_BASE}/api/portfolio/autopsy`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            alert(`Autopsia completada. Se resolvieron ${data.resolved_count} apuestas.`);
            fetchPortfolio();
        } else {
            alert(`Error en Autopsia: ${data.message || 'Desconocido'}`);
        }
      } catch (e) { console.error(e); }
    }
  };

  const handleAutotune = async () => {
    if (confirm("¿Entrenar ATHENA? Analizará todas las apuestas ganadas/perdidas y re-calibrará los parámetros matemáticos globales.")) {
      try {
        const res = await fetch(`${API_BASE}/api/autotune/run`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            setAutotuneReport(data);
        } else {
            alert(`Error en Entrenamiento: ${data.message || 'Desconocido'}`);
        }
      } catch (e) { console.error(e); }
    }
  };

  const handleResetBankroll = async () => {
    const amount = prompt("Ingresa el nuevo capital base (Bankroll Inicial):", "1000");
    if (amount !== null && !isNaN(parseFloat(amount))) {
      try {
        await fetch(`${API_BASE}/api/portfolio/reset`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ new_amount: parseFloat(amount) })
        });
        fetchPortfolio();
        alert("Bankroll reiniciado con éxito.");
      } catch (e) { console.error(e); }
    }
  };

  const fetchCalendar = async () => {
    setCalendarLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/calendar?date=${calendarDate}`);
      const data = await res.json();
      setCalendarMatches(data);
    } catch (e) {
      console.error(e);
    }
    setCalendarLoading(false);
  };

  const handleActivateOracle = async () => {
    setOracleLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/chronos/scan-day?date=${calendarDate}`);
      const data = await res.json();
      if (data.status === 'success') {
        setOracleInsights(data.value_bets);
        if (data.value_bets.length === 0) {
            alert("El oráculo escaneó todas las cuotas del día y no encontró ningún Value Bet ni opciones Ladrillo viables.");
        }
      } else {
        alert("Error del oráculo: " + data.message);
      }
    } catch (e) {
      console.error(e);
    }
    setOracleLoading(false);
  };

  useEffect(() => {
    if (activeTab === 'calendar') {
      fetchCalendar();
      setOracleInsights([]);
    } else if (activeTab === 'radar') {
      fetchMatches();
    }
  }, [calendarDate, activeTab]);

      useEffect(() => {
      fetchPortfolio();
      fetchArgosStatus();
    }, []);

  if (!isAuthenticated) {
    return (
      <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#0f172a', color: 'white'}}>
        <form onSubmit={handlePinSubmit} style={{background: 'rgba(255,255,255,0.05)', padding: '2.5rem', borderRadius: '16px', textAlign: 'center', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 20px 40px rgba(0,0,0,0.4)', width: '100%', maxWidth: '400px'}}>
          <div style={{display: 'flex', justifyContent: 'center', marginBottom: '1.5rem'}}>
             <img src="/logo.png" alt="ATHENA Logo" style={{height: '60px', objectFit: 'contain', filter: 'drop-shadow(0px 0px 8px rgba(6, 182, 212, 0.5))'}} />
          </div>
          <h2 style={{marginBottom: '0.5rem', color: '#f8fafc', letterSpacing: '2px', fontWeight: 900}}>ACCESO RESTRINGIDO</h2>
          <p style={{marginBottom: '2rem', color: '#94a3b8', fontSize: '0.9rem'}}>Ingrese su PIN de seguridad.</p>
          <input 
            type="password" 
            value={pinInput}
            onChange={(e) => setPinInput(e.target.value)}
            placeholder="****"
            maxLength={4}
            style={{
              width: '100%', padding: '1rem', fontSize: '2rem', textAlign: 'center', letterSpacing: '1rem', 
              borderRadius: '12px', border: '2px solid #334155', background: '#0f172a', color: 'white', marginBottom: '1.5rem',
              outline: 'none', transition: '0.3s'
            }}
            autoFocus
          />
          <button type="submit" style={{width: '100%', padding: '1rem', background: 'linear-gradient(90deg, #38bdf8 0%, #3b82f6 100%)', color: '#0f172a', border: 'none', borderRadius: '12px', fontWeight: 900, cursor: 'pointer', fontSize: '1.1rem', letterSpacing: '1px', textTransform: 'uppercase', transition: '0.3s'}}>
            Desbloquear
          </button>
        </form>
      </div>
    );
  }

  return (
      <>
        <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <img src="/logo.png" alt="ATHENA Logo" style={{height: '40px', objectFit: 'contain', filter: 'drop-shadow(0px 0px 8px rgba(6, 182, 212, 0.5))'}} />
            <span>ATHENA ENGINE</span>
          </div>
          <div style={{display: 'flex', gap: '1.5rem', alignItems: 'center'}}>
            <button 
              onClick={toggleArgos}
              style={{
                background: argosActive ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.05)',
                border: argosActive ? '1px solid #8b5cf6' : '1px solid rgba(255,255,255,0.1)',
                color: argosActive ? '#c4b5fd' : 'gray',
                padding: '0.5rem 1rem',
                borderRadius: 'var(--radius-pill)',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: 800,
                transition: 'var(--transition)',
                boxShadow: argosActive ? '0 0 10px rgba(139, 92, 246, 0.4)' : 'none'
              }}
            >
              👁️ ARGOS: {argosActive ? 'ON' : 'OFF'}
            </button>
            <button onClick={() => { fetchMatches(); fetchCalendar(); fetchPortfolio(); }} style={{background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', padding: '0.5rem 1rem', borderRadius: 'var(--radius-pill)', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600, transition: 'var(--transition)'}} onMouseOver={e => e.currentTarget.style.background='rgba(255,255,255,0.1)'} onMouseOut={e => e.currentTarget.style.background='rgba(255,255,255,0.05)'}>
              🔄 Actualizar
            </button>
            <div className="status-badge">
              <div className="status-dot"></div>
              SISTEMA ONLINE
            </div>
          </div>
        </div>
      </header>

      <main className="container">
        
        <div style={{display: 'flex', justifyContent: 'center'}}>
          <div className="tabs-container">
              <button onClick={() => setActiveTab('calendar')} className={`cyber-button ${activeTab === 'calendar' ? 'active' : ''}`}>📅 Chronos</button>
              <button onClick={() => setActiveTab('radar')} className={`cyber-button ${activeTab === 'radar' ? 'active' : ''}`}>🔭 Argos</button>
              <button onClick={() => setActiveTab('portfolio')} className={`cyber-button ${activeTab === 'portfolio' ? 'active' : ''}`}>💼 Plutus</button>
              <button onClick={() => { setActiveTab('lab'); fetchLab(); }} className={`cyber-button ${activeTab === 'lab' ? 'active' : ''}`}>🧬 LAB</button>
              <button onClick={() => { setActiveTab('delfos'); fetchDelfosAudit(); }} className={`cyber-button ${activeTab === 'delfos' ? 'active' : ''}`}>🔭 Delfos Audit</button>
          </div>
        </div>

        {activeTab === 'radar' && (
          <>
            <h2 className="section-title">El Oráculo de Delfos - Escáner Global</h2>
            {loading ? (
          <div className="loader-container">
            <div className="spinner"></div>
            <p style={{ color: "var(--text-muted)", fontWeight: 600 }}>Obteniendo cuotas e inicializando matrices...</p>
          </div>
        ) : matches.length === 0 ? (
          <div className="loading">No hay partidos en vivo disponibles en este momento.</div>
        ) : (
          <div className="match-grid" style={{gridTemplateColumns: '1fr'}}>
            {matches.map((match) => (
              <MatchCard key={match.id} initialMatch={match} onPlaceBet={handlePlaceBet} />
            ))}
          </div>
        )}
        </>
        )}

        {activeTab === 'calendar' && (
          <>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem'}}>
              <h2 className="section-title" style={{marginBottom: 0}}>Calendario Diario (Hora Centro)</h2>
              <div style={{display: 'flex', gap: '1rem', alignItems: 'center'}}>
                <input 
                  type="date" 
                  value={calendarDate} 
                  onChange={(e) => setCalendarDate(e.target.value)}
                  style={{padding: '0.5rem', borderRadius: '6px', background: '#1e293b', border: '1px solid #475569', color: '#f8fafc', fontWeight: 600, outline: 'none'}}
                />
                <button onClick={handleActivateOracle} disabled={oracleLoading} style={{
                  background: 'linear-gradient(90deg, #8b5cf6, #3b82f6)', border: 'none', color: 'white', padding: '0.6rem 1.2rem',
                  borderRadius: '8px', fontWeight: 800, cursor: 'pointer', boxShadow: '0 0 15px rgba(139, 92, 246, 0.4)',
                  transition: '0.2s', display: 'flex', alignItems: 'center', gap: '0.5rem'
                }}>
                  {oracleLoading ? '🔮 Escaneando Mundo...' : '👁️ Activar Oráculo'}
                </button>
              </div>
            </div>
            
            {oracleInsights.length > 0 && (
              <div className="match-card" style={{padding: '1.5rem', marginBottom: '2rem', border: '1px solid #8b5cf6', background: 'rgba(139, 92, 246, 0.1)'}}>
                <h3 style={{color: '#c4b5fd', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                  <span>👁️</span> {oracleInsights[0]?.type?.includes('Ladrillo') ? 'Plan B del Oráculo (Mejores Ladrillos de Hoy)' : 'Predicciones del Oráculo (Value Bets puros)'}
                </h3>
                <div style={{display: 'flex', flexDirection: 'column', gap: '0.8rem'}}>
                  {oracleInsights.map((insight, idx) => (
                    <div key={idx} style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px'}}>
                      <div>
                        <div style={{color: '#94a3b8', fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 700}}>
                          {insight.type && (
                            <span style={{color: insight.type.includes('Ladrillo') ? '#10b981' : '#8b5cf6', marginRight: '8px'}}>
                              {insight.type}
                            </span>
                          )}
                          {insight.league}
                        </div>
                        <div style={{color: '#f8fafc', fontWeight: 700, fontSize: '1.1rem'}}>{insight.home_team} vs {insight.away_team}</div>
                        <div style={{color: '#38bdf8', fontSize: '0.9rem', marginTop: '0.2rem', display: 'flex', gap: '0.5rem'}}>
                          <span>Pick: <strong style={{color: '#f8fafc'}}>{insight.pick}</strong></span>
                          <span>Prob: <strong style={{color: '#f8fafc'}}>{insight.prob}%</strong></span>
                          <span>Bookie: <strong style={{color: '#f8fafc'}}>{insight.bookie}</strong></span>
                        </div>
                      </div>
                      <div style={{textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end'}}>
                        <div style={{color: '#f8fafc', fontSize: '1.5rem', fontWeight: 900}}>{insight.odds}</div>
                        <div style={{color: '#10b981', fontWeight: 700, fontSize: '0.9rem', background: 'rgba(16, 185, 129, 0.2)', padding: '0.2rem 0.6rem', borderRadius: '4px'}}>
                          AVI: +{insight.edge}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {calendarLoading ? (
              <div className="loader-container">
                <div className="spinner"></div>
                <p style={{ color: "var(--text-muted)", fontWeight: 600 }}>Cargando cartelera de API-Football...</p>
              </div>
            ) : (
              <div className="match-card" style={{padding: '1.5rem', overflowX: 'auto'}}>
                <table className="data-grid">
                  <thead>
                    <tr>
                      <th>HORA</th>
                      <th>LIGA / FASE</th>
                      <th>PARTIDO</th>
                      <th style={{textAlign: 'center'}}>ESTADO</th>
                      <th style={{textAlign: 'right'}}>ACCIÓN</th>
                    </tr>
                  </thead>
                    {(() => {
                      const grouped = calendarMatches.reduce((acc, m) => {
                        const c = m.country || 'Otras Ligas';
                        if (!acc[c]) acc[c] = [];
                        acc[c].push(m);
                        return acc;
                      }, {} as Record<string, any[]>);
                      
                      return Object.entries(grouped).map(([country, matchesArray]) => (
                        <tbody key={country}>
                          <tr>
                            <td colSpan={5} 
                                onClick={() => setCollapsedCountries(prev => ({...prev, [country]: !prev[country]}))}
                                style={{ cursor: 'pointer', background: 'rgba(255,255,255,0.05)', color: '#c4b5fd', fontWeight: 800, padding: '0.8rem 1rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                                <span>📍 {country}</span>
                                <span>{collapsedCountries[country] ? '▼' : '▲'}</span>
                              </div>
                            </td>
                          </tr>
                          {!collapsedCountries[country] && matchesArray.map((cMatch: any) => (
                            <tr key={cMatch.id} style={{cursor: 'default'}}>
                              <td className="mono-font" style={{color: 'var(--cyan)', fontWeight: 800, fontSize: '1.1rem'}}>{cMatch.startTime}</td>
                              <td>
                                <div style={{color: '#f8fafc', fontWeight: 700, letterSpacing: '0.5px'}}>{cMatch.league}</div>
                                <div style={{color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.2rem', textTransform: 'uppercase'}}>{cMatch.round}</div>
                              </td>
                              <td>
                                <div style={{display: 'flex', alignItems: 'center', gap: '0.8rem', fontSize: '1.1rem', fontWeight: 700, color: '#e2e8f0'}}>
                                  <span>{cMatch.homeTeam}</span>
                                  <span style={{color: 'var(--text-dim)', fontSize: '0.9rem'}}>vs</span>
                                  <span>{cMatch.awayTeam}</span>
                                </div>
                              </td>
                              <td style={{textAlign: 'center'}}>
                                <span style={{
                                  background: cMatch.status.includes('Play') || cMatch.status.includes('Half') ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255,255,255,0.03)',
                                  color: cMatch.status.includes('Play') || cMatch.status.includes('Half') ? 'var(--primary)' : 'var(--text-muted)',
                                  padding: '0.4rem 1rem', borderRadius: 'var(--radius-pill)', fontSize: '0.8rem', fontWeight: 800, border: '1px solid ' + (cMatch.status.includes('Play') || cMatch.status.includes('Half') ? 'rgba(16, 185, 129, 0.3)' : 'transparent')
                                }}>{cMatch.status}</span>
                              </td>
                              <td style={{textAlign: 'right'}}>
                                <button style={{
                                  background: 'transparent', border: '1px solid var(--cyan)',
                                  color: 'var(--cyan)', padding: '0.6rem 1.2rem', borderRadius: 'var(--radius-pill)', fontWeight: 800,
                                  cursor: 'pointer', transition: 'var(--transition)'
                                }}
                                onMouseOver={(e) => { e.currentTarget.style.background = 'var(--cyan-glow)'; e.currentTarget.style.boxShadow = '0 0 15px var(--cyan-glow)'; }}
                                onMouseOut={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.boxShadow = 'none'; }}
                                onClick={() => { setSelectedMatch(cMatch); setActiveTab('match-detail'); }}
                                >
                                  ⚡ Analizar
                                </button>
                              </td>
                              </tr>
                            ))}
                          </tbody>
                        ));
                      })()}
                </table>
              </div>
            )}
          </>
        )}

        {activeTab === 'match-detail' && selectedMatch && (
          <MatchDashboard 
            cMatch={selectedMatch} 
            onBack={() => { setActiveTab('calendar'); setSelectedMatch(null); }} 
          />
        )}

        {activeTab === 'portfolio' && portfolio && (
          <div className="match-card">
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3rem', paddingBottom: '2rem', borderBottom: '1px solid var(--card-border)'}}>
              <div>
                <div style={{color: 'var(--text-muted)', fontWeight: 800, fontSize: '1rem', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: '0.5rem'}}>Bankroll Total</div>
                <div className="mono-font" style={{color: '#fff', fontWeight: 900, fontSize: '4rem', textShadow: '0 0 30px rgba(255,255,255,0.1)'}}>${portfolio.bankroll.toFixed(2)}</div>
              </div>
              <div style={{textAlign: 'right'}}>
                <div style={{color: 'var(--text-muted)', fontWeight: 800, fontSize: '1rem', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: '0.5rem'}}>ROI %</div>
                <div className="mono-font" style={{color: portfolio.bankroll >= portfolio.initial_bankroll ? 'var(--primary)' : 'var(--danger)', fontWeight: 900, fontSize: '4rem', textShadow: portfolio.bankroll >= portfolio.initial_bankroll ? '0 0 30px var(--primary-glow)' : '0 0 30px var(--danger-glow)'}}>
                  {portfolio.bankroll >= portfolio.initial_bankroll ? '+' : ''}{((portfolio.bankroll - portfolio.initial_bankroll) / portfolio.initial_bankroll * 100).toFixed(2)}%
                </div>
              </div>
            </div>

            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem'}}>
              <h3 className="section-title" style={{marginBottom: 0, fontSize: '1.5rem'}}>Historial de Inversiones (Ledger)</h3>
              <div style={{display: 'flex', gap: '1rem'}}>
                <button 
                  onClick={handleAutotune}
                  style={{background: 'linear-gradient(90deg, #8b5cf6, #d946ef)', color: 'white', border: 'none', padding: '0.6rem 1.5rem', borderRadius: 'var(--radius-pill)', cursor: 'pointer', fontWeight: 800, boxShadow: '0 0 15px rgba(139, 92, 246, 0.4)', transition: 'var(--transition)'}}
                >
                  🧠 Entrenar ATHENA
                </button>
                <button 
                  onClick={handleAutopsy}
                  style={{background: 'linear-gradient(90deg, var(--cyan), #3b82f6)', color: 'white', border: 'none', padding: '0.6rem 1.5rem', borderRadius: 'var(--radius-pill)', cursor: 'pointer', fontWeight: 800, boxShadow: '0 0 15px var(--cyan-glow)', transition: 'var(--transition)'}}
                >
                  🧬 Ejecutar Autopsia
                </button>
                <button 
                  onClick={handleResetBankroll}
                  style={{background: 'transparent', color: 'var(--danger)', border: '1px solid var(--danger)', padding: '0.6rem 1.5rem', borderRadius: 'var(--radius-pill)', cursor: 'pointer', fontWeight: 700, transition: 'var(--transition)'}}
                  onMouseOver={e => {e.currentTarget.style.background='var(--danger-glow)'; e.currentTarget.style.color='#fff';}}
                  onMouseOut={e => {e.currentTarget.style.background='transparent'; e.currentTarget.style.color='var(--danger)';}}
                >
                  🔄 Reset
                </button>
              </div>
            </div>
            
            {portfolio.bets.length === 0 ? (
              <div style={{color: '#94a3b8', fontStyle: 'italic'}}>No hay apuestas registradas aún.</div>
            ) : (
              <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
                {portfolio.bets.map((bet: any, index: number) => {
                  const betNumber = portfolio.bets.length - index;
                  return (
                  <div key={bet.id} style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', borderLeft: `4px solid ${bet.status === 'WON' ? '#10b981' : bet.status === 'LOST' ? '#ef4444' : bet.status === 'OPEN' ? '#38bdf8' : '#64748b'}`}}>
                    <div style={{display: 'flex', gap: '1rem', alignItems: 'center'}}>
                      <div style={{fontWeight: 900, color: 'rgba(255,255,255,0.2)', fontSize: '1.5rem', width: '30px'}}>
                        #{betNumber}
                      </div>
                      <div>
                        <div style={{fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                        {bet.pick}
                        <span style={{
                          background: bet.bet_type === 'LIVE' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(59, 130, 246, 0.2)', 
                          color: bet.bet_type === 'LIVE' ? '#ef4444' : '#3b82f6', 
                          padding: '0.1rem 0.4rem', 
                          borderRadius: '4px', 
                          fontSize: '0.65rem', 
                          fontWeight: 900
                        }}>
                          {bet.bet_type || 'PRE'}
                        </span>
                      </div>
                      <div style={{fontSize: '0.85rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.2rem'}}>
                        <span style={{color: '#cbd5e1'}}>
                          {bet.created_at ? new Date(bet.created_at + 'Z').toLocaleString('es-MX', {day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'}) : ''}
                        </span>
                        • {bet.match_id} • Cuota: 
                        {editingBetId === bet.id ? (
                          <>
                            <input type="number" step="0.01" value={editOddsValue} onChange={e => setEditOddsValue(e.target.value)} style={{width: '60px', background: '#1e293b', border: '1px solid #38bdf8', color: 'white', borderRadius: '4px', padding: '0.1rem 0.3rem', fontSize: '0.8rem'}} />
                            <button onClick={() => handleUpdateOdds(bet.id)} style={{background: '#38bdf8', color: '#0f172a', border: 'none', borderRadius: '4px', padding: '0.1rem 0.4rem', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 800}}>💾</button>
                            <button onClick={() => setEditingBetId(null)} style={{background: 'transparent', color: '#94a3b8', border: 'none', cursor: 'pointer', fontSize: '0.8rem'}}>❌</button>
                          </>
                        ) : (
                          <>
                            {bet.odds}
                            <button onClick={() => { setEditingBetId(bet.id); setEditOddsValue(bet.odds.toString()); }} style={{background: 'transparent', color: '#38bdf8', border: 'none', cursor: 'pointer', fontSize: '0.8rem', padding: '0'}}>✏️</button>
                          </>
                        )}
                      </div>
                    </div>
                    </div>
                    <div style={{textAlign: 'right'}}>
                      <div style={{fontWeight: 800, color: '#f8fafc'}}>${bet.stake}</div>
                      {bet.status === 'OPEN' ? (
                        <div style={{display: 'flex', gap: '0.5rem', marginTop: '0.5rem', justifyContent: 'flex-end'}}>
                          <button onClick={() => handleSettleBet(bet.id, 'WON')} style={{background: '#10b981', color: '#111827', border: 'none', borderRadius: '4px', padding: '0.3rem 0.6rem', cursor: 'pointer', fontWeight: 800, fontSize: '0.75rem'}}>GANADA</button>
                          <button onClick={() => handleSettleBet(bet.id, 'LOST')} style={{background: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', padding: '0.3rem 0.6rem', cursor: 'pointer', fontWeight: 800, fontSize: '0.75rem'}}>PERDIDA</button>
                          <button onClick={() => handleSettleBet(bet.id, 'REFUND')} style={{background: '#64748b', color: 'white', border: 'none', borderRadius: '4px', padding: '0.3rem 0.6rem', cursor: 'pointer', fontWeight: 800, fontSize: '0.75rem'}}>VOID</button>
                          <button onClick={() => handleDeleteBet(bet.id)} style={{background: 'rgba(239,68,68,0.2)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.4)', borderRadius: '4px', padding: '0.3rem 0.6rem', cursor: 'pointer', fontWeight: 800, fontSize: '0.75rem'}}>🗑️</button>
                        </div>
                      ) : (
                        <div style={{display: 'flex', gap: '1rem', alignItems: 'center', justifyContent: 'flex-end', marginTop: '0.5rem'}}>
                          <div style={{fontWeight: 700, fontSize: '0.85rem', color: bet.status === 'WON' ? '#10b981' : bet.status === 'LOST' ? '#ef4444' : '#64748b'}}>
                            {bet.status === 'WON' ? `+ $${bet.profit}` : bet.status === 'LOST' ? `- $${bet.stake}` : 'REEMBOLSO'}
                          </div>
                          <button onClick={() => handleDeleteBet(bet.id)} style={{background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: 'none', borderRadius: '4px', padding: '0.2rem 0.5rem', cursor: 'pointer', fontSize: '0.8rem'}}>🗑️</button>
                        </div>
                      )}
                    </div>
                  </div>
                )})}
              </div>
            )}
          </div>
        )}
                    {/* Modal Autotune Report */}
          {autotuneReport && (
            <div style={{position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, padding: '1rem'}}>
              <div style={{background: 'var(--card-bg)', padding: '2rem', borderRadius: '16px', maxWidth: '600px', width: '100%', border: '1px solid #8b5cf6', boxShadow: '0 0 30px rgba(139, 92, 246, 0.3)', maxHeight: '90vh', overflowY: 'auto'}}>
                <h2 style={{marginTop: 0, color: '#d946ef', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                  <span>🧠</span> Reporte de Entrenamiento (ATHENA)
                </h2>
                
                {/* Nueva seccion de ML Report */}
                {autotuneReport.ml_report && (
                  <div style={{background: 'rgba(139, 92, 246, 0.1)', padding: '1.5rem', borderRadius: '12px', border: '1px solid rgba(139, 92, 246, 0.3)', marginBottom: '1.5rem'}}>
                    <h3 style={{color: '#c084fc', marginTop: 0, marginBottom: '1rem', fontSize: '1.1rem'}}>Resultados Machine Learning (Random Forest)</h3>
                    <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '1rem'}}>
                      <div style={{background: 'rgba(0,0,0,0.4)', padding: '1rem', borderRadius: '8px', textAlign: 'center'}}>
                        <div style={{color: '#94a3b8', fontSize: '0.8rem', textTransform: 'uppercase'}}>Partidos Analizados</div>
                        <div style={{color: '#f8fafc', fontSize: '1.4rem', fontWeight: 900}}>{autotuneReport.ml_report.samples}</div>
                      </div>
                      <div style={{background: 'rgba(0,0,0,0.4)', padding: '1rem', borderRadius: '8px', textAlign: 'center'}}>
                        <div style={{color: '#94a3b8', fontSize: '0.8rem', textTransform: 'uppercase'}}>Precisión 1X2</div>
                        <div style={{color: '#10b981', fontSize: '1.4rem', fontWeight: 900}}>{autotuneReport.ml_report.accuracy_1x2}%</div>
                      </div>
                      <div style={{background: 'rgba(0,0,0,0.4)', padding: '1rem', borderRadius: '8px', textAlign: 'center'}}>
                        <div style={{color: '#94a3b8', fontSize: '0.8rem', textTransform: 'uppercase'}}>Precisión Goles (O/U)</div>
                        <div style={{color: '#38bdf8', fontSize: '1.4rem', fontWeight: 900}}>{autotuneReport.ml_report.accuracy_ou}%</div>
                      </div>
                      <div style={{background: 'rgba(0,0,0,0.4)', padding: '1rem', borderRadius: '8px', textAlign: 'center'}}>
                        <div style={{color: '#94a3b8', fontSize: '0.8rem', textTransform: 'uppercase'}}>Precisión BTTS</div>
                        <div style={{color: '#f59e0b', fontSize: '1.4rem', fontWeight: 900}}>{autotuneReport.ml_report.accuracy_btts}%</div>
                      </div>
                    </div>
                  </div>
                )}

                <p style={{color: 'var(--text-muted)', marginBottom: '1.5rem'}}>
                  Ajustes de Castigo Matemático (Edge Penalties) por historial de ROI en Plutus.
                </p>
                
                <div style={{maxHeight: '300px', overflowY: 'auto', marginBottom: '1.5rem'}}>
                  {(autotuneReport.report || []).map((r: any, idx: number) => (
                    <div key={idx} style={{background: 'rgba(0,0,0,0.4)', padding: '1rem', borderRadius: '8px', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                      <div>
                        <div style={{fontWeight: 800, color: '#f8fafc'}}>{r.market}</div>
                        <div style={{fontSize: '0.85rem', color: 'var(--text-muted)'}}>Muestra: {r.sample_size} apuestas</div>
                      </div>
                      <div style={{textAlign: 'right'}}>
                        <div style={{color: r.roi > 0 ? 'var(--primary)' : r.roi < 0 ? 'var(--danger)' : '#fff', fontWeight: 700}}>ROI: {r.roi}%</div>
                        {r.edge_penalty !== 0 && (
                          <div style={{fontSize: '0.85rem', color: r.edge_penalty > 0 ? '#f59e0b' : 'var(--primary)', fontWeight: 800}}>
                            Penalización Edge: {(r.edge_penalty * 100).toFixed(1)}%
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {(!autotuneReport.report || autotuneReport.report.length === 0) && (
                    <div style={{textAlign: 'center', color: '#94a3b8', padding: '1rem'}}>No hay suficientes datos procesados.</div>
                  )}
                </div>
                
                <button onClick={() => setAutotuneReport(null)} style={{width: '100%', padding: '0.8rem', background: '#8b5cf6', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 800, cursor: 'pointer'}}>
                  Entendido
                </button>
              </div>
            </div>
          )}

        {/* ── LAB TAB ─────────────────────────────────────────────────────── */}
        {activeTab === 'lab' && (
          <div className="match-card">
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem'}}>
              <div>
                <div style={{color: 'var(--text-muted)', fontWeight: 800, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: '0.3rem'}}>🧬 Laboratorio de Patrones</div>
                <div style={{color: '#fff', fontWeight: 900, fontSize: '1.5rem'}}>¿Qué combinaciones te hacen ganar?</div>
              </div>
              <button onClick={fetchLab} style={{background: '#8b5cf6', color: 'white', border: 'none', borderRadius: '8px', padding: '0.6rem 1.2rem', fontWeight: 700, cursor: 'pointer'}}>↻ Actualizar</button>
            </div>

            {labLoading && <div style={{textAlign: 'center', color: 'var(--text-muted)', padding: '3rem'}}>Analizando tus patrones...</div>}
            {!labLoading && labData && labData.status === 'sin_datos' && (
              <div style={{textAlign: 'center', color: 'var(--text-muted)', padding: '3rem'}}>{labData.message}</div>
            )}

            {!labLoading && labData && labData.status === 'ok' && (() => {
              const roiColor = (roi: number) => roi >= 10 ? '#10b981' : roi >= 0 ? '#f59e0b' : '#ef4444';
              const hitColor = (hr: number) => hr >= 65 ? '#10b981' : hr >= 50 ? '#f59e0b' : '#ef4444';

              const StatCard = ({ label, stats }: { label: string, stats: any }) => (
                <div style={{background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', padding: '0.9rem 1.1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                  <div style={{fontWeight: 700, fontSize: '0.9rem', color: '#cbd5e1', maxWidth: '55%'}}>{label}</div>
                  <div style={{display: 'flex', gap: '1.2rem', alignItems: 'center'}}>
                    <div style={{textAlign: 'center'}}>
                      <div style={{color: 'var(--text-muted)', fontSize: '0.65rem', fontWeight: 700}}>APUESTAS</div>
                      <div style={{color: '#fff', fontWeight: 900}}>{stats.total}</div>
                    </div>
                    <div style={{textAlign: 'center'}}>
                      <div style={{color: 'var(--text-muted)', fontSize: '0.65rem', fontWeight: 700}}>HIT RATE</div>
                      <div style={{color: hitColor(stats.hit_rate), fontWeight: 900}}>{stats.hit_rate}%</div>
                    </div>
                    <div style={{textAlign: 'center'}}>
                      <div style={{color: 'var(--text-muted)', fontSize: '0.65rem', fontWeight: 700}}>ROI</div>
                      <div style={{color: roiColor(stats.roi), fontWeight: 900}}>{stats.roi > 0 ? '+' : ''}{stats.roi}%</div>
                    </div>
                  </div>
                </div>
              );

              const Section = ({ title, data }: { title: string, data: Record<string, any> }) => (
                <div style={{marginBottom: '2rem'}}>
                  <div style={{color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '2px', marginBottom: '0.8rem'}}>{title}</div>
                  <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
                    {Object.entries(data).sort((a: any, b: any) => (b[1]?.roi ?? -999) - (a[1]?.roi ?? -999)).map(([key, stats]: [string, any]) =>
                      stats ? <StatCard key={key} label={key} stats={stats} /> : null
                    )}
                  </div>
                </div>
              );

              return (
                <div>
                  {/* Resumen global */}
                  <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2.5rem'}}>
                    {[
                      { label: 'Apuestas analizadas', value: labData.total_analizadas, color: '#fff' },
                      { label: 'Hit Rate Global', value: `${labData.resumen?.hit_rate}%`, color: hitColor(labData.resumen?.hit_rate ?? 0) },
                      { label: 'ROI Global', value: `${labData.resumen?.roi > 0 ? '+' : ''}${labData.resumen?.roi}%`, color: roiColor(labData.resumen?.roi ?? 0) },
                      { label: 'Ganancia Neta', value: `$${labData.resumen?.ganancia_neta?.toFixed(2)}`, color: (labData.resumen?.ganancia_neta ?? 0) >= 0 ? '#10b981' : '#ef4444' },
                    ].map(item => (
                      <div key={item.label} style={{background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '12px', padding: '1.2rem', textAlign: 'center'}}>
                        <div style={{color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem'}}>{item.label}</div>
                        <div style={{color: item.color, fontWeight: 900, fontSize: '1.6rem'}}>{item.value}</div>
                      </div>
                    ))}
                  </div>

                  {/* Patrón Dorado */}
                  {labData.patron_dorado && (
                    <div style={{background: 'linear-gradient(135deg, rgba(251,191,36,0.15), rgba(245,158,11,0.05))', border: '1px solid rgba(251,191,36,0.4)', borderRadius: '14px', padding: '1.5rem', marginBottom: '2.5rem'}}>
                      <div style={{color: '#fbbf24', fontWeight: 900, fontSize: '1rem', marginBottom: '0.8rem'}}>👑 PATRÓN DORADO — Tu combinación más rentable</div>
                      <div style={{color: '#fff', fontWeight: 800, fontSize: '1.3rem', marginBottom: '0.5rem'}}>{labData.patron_dorado.descripcion}</div>
                      <div style={{display: 'flex', gap: '2rem'}}>
                        <div><span style={{color: 'var(--text-muted)', fontSize: '0.8rem'}}>Apuestas: </span><strong style={{color: '#fff'}}>{labData.patron_dorado.total}</strong></div>
                        <div><span style={{color: 'var(--text-muted)', fontSize: '0.8rem'}}>Hit Rate: </span><strong style={{color: hitColor(labData.patron_dorado.hit_rate)}}>{labData.patron_dorado.hit_rate}%</strong></div>
                        <div><span style={{color: 'var(--text-muted)', fontSize: '0.8rem'}}>ROI: </span><strong style={{color: roiColor(labData.patron_dorado.roi)}}>{labData.patron_dorado.roi > 0 ? '+' : ''}{labData.patron_dorado.roi}%</strong></div>
                        <div><span style={{color: 'var(--text-muted)', fontSize: '0.8rem'}}>Ganancia: </span><strong style={{color: '#10b981'}}>${labData.patron_dorado.ganancia_neta?.toFixed(2)}</strong></div>
                      </div>
                    </div>
                  )}

                  {/* Mejores y peores mercados */}
                  {(labData.mejor_mercado || labData.peor_mercado) && (
                    <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2.5rem'}}>
                      {labData.mejor_mercado && (
                        <div style={{background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '10px', padding: '1rem'}}>
                          <div style={{color: '#10b981', fontWeight: 800, fontSize: '0.75rem', marginBottom: '0.3rem'}}>✅ MEJOR MERCADO</div>
                          <div style={{color: '#fff', fontWeight: 900}}>{labData.mejor_mercado}</div>
                          <div style={{color: '#10b981', fontSize: '0.85rem'}}>ROI: +{labData.por_mercado[labData.mejor_mercado]?.roi}%</div>
                        </div>
                      )}
                      {labData.peor_mercado && (
                        <div style={{background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '10px', padding: '1rem'}}>
                          <div style={{color: '#ef4444', fontWeight: 800, fontSize: '0.75rem', marginBottom: '0.3rem'}}>❌ MERCADO A EVITAR</div>
                          <div style={{color: '#fff', fontWeight: 900}}>{labData.peor_mercado}</div>
                          <div style={{color: '#ef4444', fontSize: '0.85rem'}}>ROI: {labData.por_mercado[labData.peor_mercado]?.roi}%</div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Tablas de análisis */}
                  <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem'}}>
                    <div>
                      <Section title="Por Probabilidad del Modelo" data={labData.por_probabilidad} />
                      <Section title="Por AVI (Edge)" data={labData.por_avi} />
                      <Section title="Por Confianza Hermes" data={labData.por_confianza_hermes} />
                    </div>
                    <div>
                      <Section title="Por Mercado Apostado" data={labData.por_mercado} />
                      <Section title="Por xG Total del Partido" data={labData.por_xg_total} />
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {/* 🔭 DELFOS AUDIT TAB */}
        {activeTab === 'delfos' && (
          <div className="match-card">
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem'}}>
              <div>
                <div style={{color: 'var(--text-muted)', fontWeight: 800, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: '0.3rem'}}>📡 Oráculo de Delfos</div>
                <div style={{color: '#fff', fontWeight: 900, fontSize: '1.5rem'}}>Auditoría de Rendimiento Real</div>
              </div>
              <div style={{display: 'flex', gap: '0.5rem'}}>
                  <button onClick={handleAutopsy} style={{background: '#eab308', color: 'black', border: 'none', borderRadius: '8px', padding: '0.6rem 1.2rem', fontWeight: 700, cursor: 'pointer'}}>🔥 Actualizar Resultados</button>
                  <button onClick={() => setShowDiagnostic(!showDiagnostic)} style={{background: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', padding: '0.6rem 1.2rem', fontWeight: 700, cursor: 'pointer'}}>📊 Diagnóstico</button>
                  <button onClick={fetchDelfosAudit} style={{background: '#8b5cf6', color: 'white', border: 'none', borderRadius: '8px', padding: '0.6rem 1.2rem', fontWeight: 700, cursor: 'pointer'}}>🔄 Recargar</button>
                </div>
            </div>
            
            {showDiagnostic && delfosDiagnostic && (
              <div style={{background: 'rgba(59, 130, 246, 0.1)', border: '1px solid #3b82f6', padding: '1.5rem', borderRadius: '12px', marginBottom: '2rem'}}>
                <h3 style={{color: '#60a5fa', marginBottom: '1rem'}}>Diagnóstico de Integridad (Ledger)</h3>
                <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1rem'}}>
                    <div>Total Bets: <strong>{delfosDiagnostic.total}</strong></div>
                    <div>Con Snapshot: <strong>{delfosDiagnostic.has_snap}</strong></div>
                    <div>Sin Snapshot: <strong>{delfosDiagnostic.no_snap}</strong></div>
                    <div>Excluidos/Mock: <strong>{delfosDiagnostic.mock_matches}</strong></div>
                </div>
                <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>OPEN: {delfosDiagnostic.status_counts?.OPEN || 0} | WON: {delfosDiagnostic.status_counts?.WON || 0} | LOST: {delfosDiagnostic.status_counts?.LOST || 0}</div>
                {delfosDiagnostic.excluidos?.length > 0 && (
                  <div style={{marginTop: '1rem', background: '#1e293b', padding: '1rem', borderRadius: '8px', maxHeight: '150px', overflowY: 'auto'}}>
                    <div style={{color: '#ef4444', fontWeight: 'bold', marginBottom: '0.5rem'}}>Registros Omitidos:</div>
                    {delfosDiagnostic.excluidos.map((ex: any) => (
                      <div key={ex.id} style={{fontSize: '0.8rem', color: '#94a3b8'}}>- [{ex.id}] {ex.pick} (Match: {ex.match_id}) {ex.evidence_snapshot ? 'ID NO VERIFICABLE' : 'SIN EVIDENCIA'}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {delfosLoading && <div style={{textAlign: 'center', color: 'var(--text-muted)', padding: '3rem'}}>Obteniendo registros...</div>}

            {!delfosLoading && delfosAuditData && (
              <div>
                <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem'}}>
                  <div style={{background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--card-border)'}}>
                    <div style={{color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 800, textTransform: 'uppercase', marginBottom: '0.5rem'}}>Total Resueltos</div>
                    <div style={{fontSize: '2rem', fontWeight: 900}}>{delfosAuditData.resumen.total_resueltos}</div>
                  </div>
                  <div style={{background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--card-border)'}}>
                    <div style={{color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 800, textTransform: 'uppercase', marginBottom: '0.5rem'}}>Hit Rate Global</div>
                    <div style={{fontSize: '2rem', fontWeight: 900, color: delfosAuditData.resumen.hit_rate >= 50 ? '#10b981' : '#ef4444'}}>{delfosAuditData.resumen.hit_rate}%</div>
                  </div>
                  <div style={{background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--card-border)'}}>
                    <div style={{color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 800, textTransform: 'uppercase', marginBottom: '0.5rem'}}>ROI Teórico (Plano)</div>
                    <div style={{fontSize: '2rem', fontWeight: 900, color: delfosAuditData.resumen.roi_teorico >= 0 ? '#10b981' : '#ef4444'}}>{delfosAuditData.resumen.roi_teorico > 0 ? '+' : ''}{delfosAuditData.resumen.roi_teorico}%</div>
                  </div>
                </div>

                <div style={{marginBottom: '2rem'}}>
                  <h3 style={{fontSize: '1.2rem', marginBottom: '1rem'}}>Rendimiento por Mercado Recomendado</h3>
                  <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
                    {Object.entries(delfosAuditData.por_mercado).map(([market, data]: [string, any]) => (
                      <div key={market} style={{display: 'flex', justifyContent: 'space-between', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--card-border)'}}>
                        <div style={{fontWeight: 800}}>{market}</div>
                        <div style={{display: 'flex', gap: '2rem', width: '60%', justifyContent: 'flex-end'}}>
                          <div style={{textAlign: 'right'}}><span style={{color: 'var(--text-muted)', fontSize: '0.7rem', display: 'block'}}>PICKS</span><span style={{fontWeight: 800}}>{data.total}</span></div>
                          <div style={{textAlign: 'right'}}><span style={{color: 'var(--text-muted)', fontSize: '0.7rem', display: 'block'}}>HIT RATE</span><span style={{fontWeight: 800, color: data.hit_rate >= 50 ? '#10b981' : '#ef4444'}}>{data.hit_rate}%</span></div>
                          <div style={{textAlign: 'right', minWidth: '70px'}}><span style={{color: 'var(--text-muted)', fontSize: '0.7rem', display: 'block'}}>ROI</span><span style={{fontWeight: 800, color: data.roi >= 0 ? '#10b981' : '#ef4444'}}>{data.roi > 0 ? '+' : ''}{data.roi}%</span></div>
                        </div>
                      </div>
                    ))}
                    {Object.keys(delfosAuditData.por_mercado).length === 0 && <div style={{color: 'var(--text-muted)'}}>No hay suficientes datos resueltos.</div>}
                  </div>
                </div>

                {delfosAuditData.picks_hoy.length > 0 && (
                  <div style={{marginBottom: '2rem'}}>
                    <h3 style={{fontSize: '1.2rem', marginBottom: '1rem'}}>Recomendaciones Activas (Hoy)</h3>
                    <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
                      {delfosAuditData.picks_hoy.map((pick: any) => (
                        <div key={pick.id} style={{display: 'flex', justifyContent: 'space-between', background: 'rgba(59, 130, 246, 0.1)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.3)'}}>
                          <div>
                            <div style={{fontWeight: 800}}>{pick.home_team} vs {pick.away_team}</div>
                            <div style={{fontSize: '0.8rem', color: '#60a5fa'}}>{pick.pick} • {pick.tipo}</div>
                          </div>
                          <div style={{textAlign: 'right'}}>
                            <div style={{fontWeight: 800, color: 'var(--text-muted)'}}>{pick.cuota}</div>
                            <div style={{fontSize: '0.8rem', color: '#60a5fa'}}>{pick.probabilidad}% Prob</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <h3 style={{fontSize: '1.2rem', marginBottom: '1rem'}}>Historial Reciente</h3>
                  <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
                    {delfosAuditData.historial.map((pick: any) => (
                      <div key={pick.id} style={{display: 'flex', justifyContent: 'space-between', background: pick.es_correcto === 1 ? 'rgba(16, 185, 129, 0.05)' : pick.es_correcto === -1 ? 'rgba(156, 163, 175, 0.05)' : 'rgba(239, 68, 68, 0.05)', padding: '1rem', borderRadius: '8px', border: `1px solid ${pick.es_correcto === 1 ? 'rgba(16, 185, 129, 0.2)' : pick.es_correcto === -1 ? 'rgba(156, 163, 175, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`}}>
                        <div>
                          <div style={{fontWeight: 800}}>{pick.home_team} vs {pick.away_team}</div>
                          <div style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>{pick.fecha} • {pick.pick}</div>
                        </div>
                        <div style={{textAlign: 'right', display: 'flex', alignItems: 'center', gap: '1rem'}}>
                          <div style={{fontWeight: 900, fontSize: '1.1rem'}}>{pick.resultado}</div>
                          {pick.es_correcto === 1 ? (
                            <div style={{background: '#10b981', color: 'white', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 800}}>WIN</div>
                          ) : pick.es_correcto === -1 ? (
                            <div style={{background: '#6b7280', color: 'white', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 800}}>REFUND</div>
                          ) : (
                            <div style={{background: '#ef4444', color: 'white', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 800}}>LOSS</div>
                          )}
                        </div>
                      </div>
                    ))}
                    {delfosAuditData.historial.length === 0 && <div style={{color: 'var(--text-muted)'}}>No hay historial de picks.</div>}
                  </div>
                </div>

              </div>
            )}
          </div>
        )}

      </main>
    </>
  );
}



