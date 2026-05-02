export default function Percepts({ agentState, lastStep }) {
  const percept = lastStep?.percept || { breeze: false, stench: false, glitter: false }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12, minWidth: 200 }}>

      {/* Sensory Readings */}
      <div style={{
        background: '#fff8ee', border: '1px solid #c8a870',
        borderRadius: 8, padding: '14px 16px',
        boxShadow: '0 2px 8px #c8a87022'
      }}>
        <div style={{ fontSize: '0.6rem', color: '#b89060', letterSpacing: '0.12em', marginBottom: 10, textTransform: 'uppercase' }}>
          Sensory Readings — ({agentState.pos[0]},{agentState.pos[1]})
        </div>
        {[
          { icon: '💨', lbl: 'Draught',    sub: '(Abyss nearby)',   active: percept.breeze  },
          { icon: '🌫️', lbl: 'Fetor',      sub: '(Beast nearby)',   active: percept.stench  },
          { icon: '✨', lbl: 'Glint',      sub: '(Relic here)',     active: percept.glitter },
        ].map(({ icon, lbl, sub, active }) => (
          <div key={lbl} style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '8px 12px', borderRadius: 5, marginBottom: 6,
            background: active ? '#fffbeb' : '#f9f2e8',
            border: `1px solid ${active ? '#d97706' : '#c8a870'}`,
            opacity: active ? 1 : 0.5, transition: 'all 0.3s'
          }}>
            <span style={{ fontSize: '1.2rem' }}>{icon}</span>
            <div>
              <div style={{ fontSize: '0.78rem', fontWeight: 'bold', color: active ? '#b45309' : '#8b6340' }}>{lbl}</div>
              <div style={{ fontSize: '0.6rem', color: '#b89060', fontStyle: 'italic' }}>{sub}</div>
            </div>
            <div style={{ marginLeft: 'auto', fontSize: '0.7rem', fontWeight: 'bold', color: active ? '#2e7d32' : '#b89060' }}>
              {active ? 'ACTIVE' : '—'}
            </div>
          </div>
        ))}
      </div>

      {/* Stats */}
      <div style={{
        background: '#fff8ee', border: '1px solid #c8a870',
        borderRadius: 8, padding: '14px 16px',
        boxShadow: '0 2px 8px #c8a87022'
      }}>
        <div style={{ fontSize: '0.6rem', color: '#b89060', letterSpacing: '0.12em', marginBottom: 10, textTransform: 'uppercase' }}>
          Agent Statistics
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 16px' }}>
          {[
            { lbl: 'Visited',      val: agentState.visited.length,  col: '#3b2a14' },
            { lbl: 'Proven Safe',  val: agentState.safe.length,     col: '#2e7d32' },
            { lbl: 'Marked Peril', val: agentState.danger.length,   col: '#c62828' },
            { lbl: 'KB Clauses',   val: agentState.kb_clause_count, col: '#6a1b9a' },
          ].map(({ lbl, val, col }) => (
            <div key={lbl}>
              <div style={{ fontSize: '0.58rem', color: '#b89060', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{lbl}</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: col }}>{val}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Symbol key */}
      <div style={{
        background: '#fff8ee', border: '1px solid #c8a870',
        borderRadius: 8, padding: '12px 16px',
        boxShadow: '0 2px 8px #c8a87022'
      }}>
        <div style={{ fontSize: '0.6rem', color: '#b89060', letterSpacing: '0.12em', marginBottom: 8, textTransform: 'uppercase' }}>
          Legend
        </div>
        {[
          ['🧭', 'Explorer (you)'],
          ['🌀', 'Abyss (pit)'],
          ['🦂', 'The Beast'],
          ['🔮', 'The Relic'],
        ].map(([ic, lbl]) => (
          <div key={lbl} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 5 }}>
            <span style={{ fontSize: '1rem' }}>{ic}</span>
            <span style={{ fontSize: '0.72rem', color: '#8b6340', fontStyle: 'italic' }}>{lbl}</span>
          </div>
        ))}
      </div>
    </div>
  )
}