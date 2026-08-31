import re

with open('frontend/src/app/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'<button onClick=\{fetchDelfosAudit\}.*?>.*?Actualizar</button>\n\s*</div>', re.DOTALL)
match = pattern.search(content)

if match:
    new_ui = '''<div style={{display: 'flex', gap: '0.5rem'}}>
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
            )}'''
            
    content = content[:match.start()] + new_ui + content[match.end():]
    with open('frontend/src/app/page.tsx', 'w', encoding='utf-8') as f:
        f.write(content)
else:
    print("Could not find button to replace")
