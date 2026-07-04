"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

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
    main_line: { pick: string; prob: number; odds: number; } | null;
    medium_risk: { pick: string; prob: number; odds: number; edge: number; kelly_percent: number; bookmaker: string; } | null;
    dreamer: { pick: string; prob: number; fair_odds: number; } | null;
    ultra: { pick: string; prob: number; fair_odds: number; } | null;
    corners_alert?: { pick: string; prob: number; fair_odds: number; } | null;
    player_prop?: { player: string; pick: string; prob: number; fair_odds: number; } | null;
    is_ensembled?: boolean;
  };
}

const MatchCard = ({ initialMatch, onPlaceBet }: { initialMatch: Match, onPlaceBet: any }) => {
  const [match, setMatch] = useState(initialMatch);
  const [liveMinute, setLiveMinute] = useState(0);
  const [liveHomeGoals, setLiveHomeGoals] = useState(0);
  const [liveAwayGoals, setLiveAwayGoals] = useState(0);
  const [isCalculating, setIsCalculating] = useState(false);
  const [arbCapital, setArbCapital] = useState(1000);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isAutoPlaying && liveMinute < 90) {
      interval = setInterval(() => {
        setLiveMinute(m => {
          const newMinute = m + 1;
          
          // Lógica de Goles Aleatorios basados en distribución muy básica
          // (aprox. 1 gol cada 30-40 minutos por equipo)
          if (Math.random() < 0.02) {
             setLiveHomeGoals(g => g + 1);
          } else if (Math.random() < 0.02) {
             setLiveAwayGoals(g => g + 1);
          }
          
          return newMinute;
        });
      }, 1500); // 1 minuto de partido = 1.5 segundos en la vida real
    } else if (liveMinute >= 90) {
      setIsAutoPlaying(false);
    }
    return () => clearInterval(interval);
  }, [isAutoPlaying, liveMinute]);

  // Hook secundario: Cuando cambia el marcador/minuto en AutoPlay, llamar API
  useEffect(() => {
    if (isAutoPlaying) {
      calculateLive();
    }
  }, [liveMinute, liveHomeGoals, liveAwayGoals]);

  const calculateLive = async () => {
    setIsCalculating(true);
    try {
      const res = await fetch(`${API_BASE}/api/live-analysis`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            homeTeam: match.homeTeam, awayTeam: match.awayTeam,
            minute: liveMinute, homeGoals: liveHomeGoals, awayGoals: liveAwayGoals,
            currentOdds: match.odds
        })
      });
      const data = await res.json();
      setMatch({ ...match, analysis: data.analysis, score: `${liveHomeGoals} - ${liveAwayGoals}` });
    } catch (e) {
      console.error(e);
    }
    setIsCalculating(false);
  };

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

      <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginTop: '1rem'}}>
        
        <div style={{background: 'linear-gradient(180deg, #dcfce7 0%, #f0fdf4 100%)', border: '1px solid #86efac', borderRadius: '16px', padding: '1.5rem', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'}}>
          <div style={{color: '#047857', fontWeight: 800, fontSize: '0.85rem', letterSpacing: '1px', marginBottom: '1rem'}}>🟢 MAIN LINE (SEGURA)</div>
          {match.analysis?.main_line ? (
            <div>
              <div style={{fontSize: '1.25rem', fontWeight: 700, color: '#0f172a'}}>{match.analysis.main_line.pick}</div>
              <div style={{display: 'flex', flexDirection: 'column', marginTop: '0.8rem', gap: '0.2rem'}}>
                <span style={{color: '#334155', fontSize: '0.9rem', fontWeight: 500}}>Prob: <span style={{color: '#047857', fontWeight: 700}}>{match.analysis.main_line.prob}%</span></span>
                {match.analysis.main_line.odds > 0 && <span style={{color: '#334155', fontSize: '0.9rem', fontWeight: 500}}>Cuota Inicial: {match.analysis.main_line.odds.toFixed(2)}</span>}
              </div>
            </div>
          ) : (
            <div style={{color: '#475569', fontStyle: 'italic', fontSize: '0.9rem', marginTop: '1rem', fontWeight: 500}}>Sin línea segura.</div>
          )}
        </div>

        <div style={{background: 'linear-gradient(180deg, #fef3c7 0%, #fffbeb 100%)', border: '1px solid #fcd34d', borderRadius: '16px', padding: '1.5rem', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'}}>
          <div style={{color: '#b45309', fontWeight: 800, fontSize: '0.85rem', letterSpacing: '1px', marginBottom: '1rem'}}>🟡 LÍNEA DE VALOR (EDGE)</div>
          {match.analysis?.medium_risk ? (
            <div>
              <div style={{fontSize: '1.25rem', fontWeight: 700, color: '#0f172a'}}>{match.analysis.medium_risk.pick}</div>
              <div style={{display: 'flex', flexDirection: 'column', marginTop: '0.8rem', gap: '0.2rem'}}>
                <span style={{color: '#334155', fontSize: '0.9rem', fontWeight: 500}}>Edge Inicial: <span style={{color: '#d97706', fontWeight: 700}}>+{match.analysis.medium_risk.edge}%</span></span>
                <span style={{color: '#334155', fontSize: '0.9rem', fontWeight: 500}}>Inversión: <span style={{color: '#0f172a', fontWeight: 700}}>{match.analysis.medium_risk.kelly_percent}% Bank</span></span>
              </div>
              <button 
                onClick={() => onPlaceBet(match.id, match.analysis.medium_risk?.pick, match.analysis.medium_risk?.odds, match.analysis.medium_risk?.kelly_percent)}
                style={{marginTop: '1rem', width: '100%', padding: '0.5rem', background: '#d97706', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 700, cursor: 'pointer'}}
              >
                + Rastrear Apuesta
              </button>
            </div>
          ) : (
            <div style={{color: '#475569', fontStyle: 'italic', fontSize: '0.9rem', marginTop: '1rem', fontWeight: 500}}>Sin valor detectado.</div>
          )}
        </div>

        {/* TIER: DATOS ALTERNATIVOS (CORNERS) */}
        <div style={{background: 'linear-gradient(180deg, #e0f2fe 0%, #f0f9ff 100%)', border: '1px solid #7dd3fc', borderRadius: '16px', padding: '1.5rem', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'}}>
          <div style={{color: '#0369a1', fontWeight: 800, fontSize: '0.85rem', letterSpacing: '1px', marginBottom: '1rem'}}>🔵 ALTERNATIVO (CORNERS)</div>
          {match.analysis?.corners_alert ? (
            <div>
              <div style={{fontSize: '1.25rem', fontWeight: 700, color: '#0f172a'}}>{match.analysis.corners_alert.pick}</div>
              <div style={{display: 'flex', flexDirection: 'column', marginTop: '0.8rem', gap: '0.2rem'}}>
                <span style={{color: '#334155', fontSize: '0.9rem', fontWeight: 500}}>Prob: <span style={{color: '#0369a1', fontWeight: 700}}>{match.analysis.corners_alert.prob}%</span></span>
                <span style={{color: '#334155', fontSize: '0.9rem', fontWeight: 500}}>Fair Odds: {match.analysis.corners_alert.fair_odds.toFixed(2)}</span>
              </div>
            </div>
          ) : (
            <div style={{color: '#475569', fontStyle: 'italic', fontSize: '0.9rem', marginTop: '1rem', fontWeight: 500}}>Sin predicción sólida.</div>
          )}
        </div>

        {/* TIER: PLAYER PROPS */}
        <div style={{background: 'linear-gradient(180deg, #ffedd5 0%, #fff7ed 100%)', border: '1px solid #fdba74', borderRadius: '16px', padding: '1.5rem', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'}}>
          <div style={{color: '#c2410c', fontWeight: 800, fontSize: '0.85rem', letterSpacing: '1px', marginBottom: '1rem'}}>🎯 PLAYER PROPS</div>
          {match.analysis?.player_prop ? (
            <div>
              <div style={{fontSize: '1.1rem', fontWeight: 800, color: '#c2410c'}}>{match.analysis.player_prop.player}</div>
              <div style={{fontSize: '1.1rem', fontWeight: 600, color: '#0f172a', marginTop: '0.3rem'}}>{match.analysis.player_prop.pick}</div>
              <div style={{display: 'flex', flexDirection: 'column', marginTop: '0.8rem', gap: '0.2rem'}}>
                <span style={{color: '#334155', fontSize: '0.9rem', fontWeight: 500}}>Edge IA: <span style={{color: '#c2410c', fontWeight: 700}}>{match.analysis.player_prop.prob}%</span></span>
                <span style={{color: '#334155', fontSize: '0.9rem', fontWeight: 500}}>Fair Odds: {match.analysis.player_prop.fair_odds.toFixed(2)}</span>
              </div>
            </div>
          ) : (
            <div style={{color: '#475569', fontStyle: 'italic', fontSize: '0.9rem', marginTop: '1rem', fontWeight: 500}}>Datos insuficientes para estrellas.</div>
          )}
        </div>

        <div style={{background: 'linear-gradient(180deg, #fee2e2 0%, #fef2f2 100%)', border: '1px solid #fca5a5', borderRadius: '16px', padding: '1.5rem', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'}}>
          <div style={{color: '#b91c1c', fontWeight: 800, fontSize: '0.85rem', letterSpacing: '1px', marginBottom: '1rem'}}>🔴 SOÑADORA (MARCADOR)</div>
          {match.analysis?.dreamer && (
            <div>
              <div style={{fontSize: '1.25rem', fontWeight: 700, color: '#0f172a'}}>{match.analysis.dreamer.pick}</div>
              <div style={{display: 'flex', flexDirection: 'column', marginTop: '0.8rem', gap: '0.2rem'}}>
                <span style={{color: '#334155', fontSize: '0.9rem', fontWeight: 500}}>Prob: <span style={{color: '#b91c1c', fontWeight: 700}}>{match.analysis.dreamer.prob}%</span></span>
                <span style={{color: '#334155', fontSize: '0.9rem', fontWeight: 500}}>Cuota Justa: <span style={{color: '#0f172a', fontWeight: 700}}>{match.analysis.dreamer.fair_odds.toFixed(2)}</span></span>
              </div>
            </div>
          )}
        </div>

        <div style={{background: 'linear-gradient(180deg, #f3e8ff 0%, #faf5ff 100%)', border: '1px solid #d8b4fe', borderRadius: '16px', padding: '1.5rem', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'}}>
          <div style={{color: '#7e22ce', fontWeight: 800, fontSize: '0.85rem', letterSpacing: '1px', marginBottom: '1rem'}}>🟣 ULTRA (SÚPER PARLAY)</div>
          {match.analysis?.ultra && (
            <div>
              <div style={{fontSize: '1.0rem', fontWeight: 700, color: '#0f172a', lineHeight: 1.2}}>{match.analysis.ultra.pick}</div>
              <div style={{display: 'flex', flexDirection: 'column', marginTop: '0.8rem', gap: '0.2rem'}}>
                <span style={{color: '#334155', fontSize: '0.9rem', fontWeight: 500}}>Prob: <span style={{color: '#7e22ce', fontWeight: 700}}>{match.analysis.ultra.prob}%</span></span>
                <span style={{color: '#334155', fontSize: '0.9rem', fontWeight: 500}}>Cuota Justa: <span style={{color: '#0f172a', fontWeight: 700}}>{match.analysis.ultra.fair_odds.toFixed(2)}</span></span>
              </div>
            </div>
          )}
        </div>

      </div>

      <div style={{ marginTop: '2rem', padding: '1.5rem', background: '#0f172a', borderRadius: '12px', border: '1px solid #334155' }}>
          <h4 style={{ margin: '0 0 1.2rem 0', color: '#94a3b8', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{width: '8px', height: '8px', background: '#ef4444', borderRadius: '50%', boxShadow: '0 0 8px #ef4444', animation: 'pulse 2s infinite'}}></div>
            Laboratorio En Vivo (Time Decay)
          </h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'flex-end' }}>
              <div>
                  <label style={{display:'block', fontSize:'0.8rem', color:'#cbd5e1', marginBottom:'0.4rem'}}>Minuto (0-90)</label>
                  <input type="number" min="0" max="90" value={liveMinute} onChange={e => setLiveMinute(parseInt(e.target.value)||0)} style={{width:'80px', padding:'0.6rem', borderRadius:'6px', background:'#1e293b', border:'1px solid #475569', color:'white'}} />
              </div>
              <div>
                  <label style={{display:'block', fontSize:'0.8rem', color:'#cbd5e1', marginBottom:'0.4rem'}}>Goles {match.homeTeam}</label>
                  <input type="number" min="0" value={liveHomeGoals} onChange={e => setLiveHomeGoals(parseInt(e.target.value)||0)} style={{width:'80px', padding:'0.6rem', borderRadius:'6px', background:'#1e293b', border:'1px solid #475569', color:'white'}} />
              </div>
              <div>
                  <label style={{display:'block', fontSize:'0.8rem', color:'#cbd5e1', marginBottom:'0.4rem'}}>Goles {match.awayTeam}</label>
                  <input type="number" min="0" value={liveAwayGoals} onChange={e => setLiveAwayGoals(parseInt(e.target.value)||0)} style={{width:'80px', padding:'0.6rem', borderRadius:'6px', background:'#1e293b', border:'1px solid #475569', color:'white'}} />
              </div>
              <button 
                  onClick={calculateLive} 
                  disabled={isCalculating || isAutoPlaying} 
                  style={{background: 'linear-gradient(90deg, #3b82f6 0%, #2563eb 100%)', color:'white', border:'none', padding:'0.6rem 1.2rem', borderRadius:'6px', cursor: (isCalculating || isAutoPlaying) ? 'not-allowed' : 'pointer', fontWeight:600, transition:'0.2s', opacity: (isCalculating || isAutoPlaying) ? 0.5 : 1}}
              >
                  Recalcular Manual
              </button>
              <button 
                  onClick={() => setIsAutoPlaying(!isAutoPlaying)}
                  style={{background: isAutoPlaying ? '#ef4444' : 'linear-gradient(90deg, #10b981 0%, #059669 100%)', color:'white', border:'none', padding:'0.6rem 1.2rem', borderRadius:'6px', cursor:'pointer', fontWeight:600, transition:'0.2s', display: 'flex', alignItems: 'center', gap: '0.4rem'}}
              >
                  {isAutoPlaying ? '⏹️ Detener Simulación' : '▶️ Iniciar Partido Live'}
              </button>
          </div>
          <p style={{color: '#64748b', fontSize: '0.75rem', marginTop: '1rem'}}>
            El motor automático avanzará el reloj 1 minuto cada 1.5 segundos, inyectando goles basándose en la varianza matemática (Poisson) y recalculando todo el panel en tiempo real.
          </p>
      </div>
    </div>
  );
}

export default function Home() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'radar' | 'portfolio'>('radar');
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);

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

  const handlePlaceBet = async (matchId: string, pick: string, odds: number, kellyPercent: number) => {
    if (!portfolio) return;
    const stake = portfolio.bankroll * (kellyPercent / 100);
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/bet`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ match_id: matchId, pick, odds, stake })
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
      const res = await fetch(`${API_BASE}/api/portfolio/settle`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bet_id: betId, result })
      });
      fetchPortfolio();
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    fetchMatches();
    fetchPortfolio();
    const interval = setInterval(() => {
        fetchMatches();
        fetchPortfolio();
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            ⚡ <span>TipsterAI Quad-Core</span>
          </div>
          <div className="status-badge" style={{background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', border: '1px solid rgba(59, 130, 246, 0.2)'}}>
            <div className="status-dot" style={{backgroundColor: '#3b82f6', boxShadow: '0 0 10px #3b82f6'}}></div>
            Motor En Vivo (Time Decay)
          </div>
        </div>
      </header>

      <main className="container" style={{maxWidth: '1200px'}}>
        
        <div style={{display: 'flex', gap: '1rem', marginBottom: '2rem'}}>
            <button onClick={() => setActiveTab('radar')} style={{padding: '0.8rem 2rem', borderRadius: '8px', border: 'none', background: activeTab === 'radar' ? '#3b82f6' : '#e2e8f0', color: activeTab === 'radar' ? 'white' : '#475569', fontWeight: 700, cursor: 'pointer', transition: '0.2s'}}>📡 Radar Quant</button>
            <button onClick={() => setActiveTab('portfolio')} style={{padding: '0.8rem 2rem', borderRadius: '8px', border: 'none', background: activeTab === 'portfolio' ? '#3b82f6' : '#e2e8f0', color: activeTab === 'portfolio' ? 'white' : '#475569', fontWeight: 700, cursor: 'pointer', transition: '0.2s'}}>💼 Mi Portafolio</button>
        </div>

        {activeTab === 'radar' && (
          <>
            <h2 className="section-title">Escáner de Oportunidades - Mundial 2026</h2>
            {loading ? (
          <div className="loader-container">
            <div className="spinner"></div>
            <p style={{ color: "var(--text-muted)", fontWeight: 600 }}>Obteniendo cuotas e inicializando matrices...</p>
          </div>
        ) : matches.length === 0 ? (
          <div className="loading">No hay partidos del Mundial disponibles en este momento.</div>
        ) : (
          <div className="match-grid" style={{gridTemplateColumns: '1fr'}}>
            {matches.map((match) => (
              <MatchCard key={match.id} initialMatch={match} onPlaceBet={handlePlaceBet} />
            ))}
          </div>
        )}
        </>
        )}

        {activeTab === 'portfolio' && portfolio && (
          <div style={{background: '#ffffff', borderRadius: '16px', padding: '2rem', boxShadow: '0 10px 25px rgba(0,0,0,0.05)'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', paddingBottom: '1rem', borderBottom: '1px solid #e2e8f0'}}>
              <div>
                <div style={{color: '#64748b', fontWeight: 700, fontSize: '0.9rem', textTransform: 'uppercase'}}>Bankroll Total</div>
                <div style={{color: '#0f172a', fontWeight: 900, fontSize: '2.5rem'}}>${portfolio.bankroll.toFixed(2)}</div>
              </div>
              <div style={{textAlign: 'right'}}>
                <div style={{color: '#64748b', fontWeight: 700, fontSize: '0.9rem', textTransform: 'uppercase'}}>ROI %</div>
                <div style={{color: portfolio.bankroll >= portfolio.initial_bankroll ? '#10b981' : '#ef4444', fontWeight: 900, fontSize: '2.5rem'}}>
                  {((portfolio.bankroll - portfolio.initial_bankroll) / portfolio.initial_bankroll * 100).toFixed(2)}%
                </div>
              </div>
            </div>

            <h3 style={{color: '#0f172a', marginBottom: '1rem'}}>Historial de Inversiones</h3>
            {portfolio.bets.length === 0 ? (
              <div style={{color: '#64748b', fontStyle: 'italic'}}>No hay apuestas registradas aún.</div>
            ) : (
              <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
                {portfolio.bets.map((bet: any) => (
                  <div key={bet.id} style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: '#f8fafc', borderRadius: '8px', borderLeft: `4px solid ${bet.status === 'win' ? '#10b981' : bet.status === 'lose' ? '#ef4444' : '#f59e0b'}`}}>
                    <div>
                      <div style={{fontWeight: 700, color: '#0f172a'}}>{bet.pick}</div>
                      <div style={{fontSize: '0.85rem', color: '#64748b'}}>{bet.date} • Cuota: {bet.odds}</div>
                    </div>
                    <div style={{textAlign: 'right'}}>
                      <div style={{fontWeight: 800, color: '#0f172a'}}>${bet.stake}</div>
                      {bet.status === 'pending' ? (
                        <div style={{display: 'flex', gap: '0.5rem', marginTop: '0.5rem'}}>
                          <button onClick={() => handleSettleBet(bet.id, 'win')} style={{background: '#10b981', color: 'white', border: 'none', borderRadius: '4px', padding: '0.3rem 0.6rem', cursor: 'pointer', fontWeight: 700, fontSize: '0.75rem'}}>GANADA</button>
                          <button onClick={() => handleSettleBet(bet.id, 'lose')} style={{background: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', padding: '0.3rem 0.6rem', cursor: 'pointer', fontWeight: 700, fontSize: '0.75rem'}}>PERDIDA</button>
                        </div>
                      ) : (
                        <div style={{fontWeight: 700, fontSize: '0.85rem', color: bet.status === 'win' ? '#10b981' : '#ef4444'}}>
                          {bet.status === 'win' ? `+ $${bet.expected_return}` : `- $${bet.stake}`}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </>
  );
}
