export default function StatsBar({ totalSteps, kbClauses, gameState }) {
  return (
    <div style={{ display: 'flex', gap: 28, alignItems: 'center' }}>
      {[
        { lbl: 'Deductions',  val: totalSteps.toLocaleString(), col: '#f5ede0' },
        { lbl: 'KB Clauses',  val: kbClauses,                   col: '#c8a870' },
        { lbl: 'Status',      val: gameState === 'won'   ? 'Victory'  :
                                   gameState === 'dead'  ? 'Fallen'   :
                                   gameState === 'stuck' ? 'Trapped'  :
                                   gameState === 'running' ? 'Delving' : '—',
          col: gameState === 'won'  ? '#86efac' :
               gameState === 'dead' ? '#fca5a5' : '#f5ede0' },
      ].map(({ lbl, val, col }) => (
        <div key={lbl} style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.58rem', color: '#c8a870', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{lbl}</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: col, fontFamily: 'Georgia,serif' }}>{val}</div>
        </div>
      ))}
    </div>
  )
}