import { btnStyle } from '../App'

export default function Controls({
  rows, setRows, cols, setCols, numPits, setNumPits,
  onNew, onStep, onAuto, onReveal,
  auto, reveal, gameState
}) {
  return (
    <div style={{
      background: '#fff8ee', border: '1px solid #c8a870',
      borderRadius: 8, padding: '14px 18px',
      display: 'flex', flexWrap: 'wrap', gap: '14px', alignItems: 'flex-end',
      boxShadow: '0 2px 8px #c8a87022'
    }}>
      {[
        { lbl: 'Rows',    val: rows,    set: setRows,    min: 3, max: 8 },
        { lbl: 'Columns', val: cols,    set: setCols,    min: 3, max: 8 },
        { lbl: 'Abysses', val: numPits, set: setNumPits, min: 1, max: Math.max(1, Math.floor(rows * cols / 3)) },
      ].map(({ lbl, val, set, min, max }) => (
        <div key={lbl}>
          <div style={{ fontSize: '0.6rem', color: '#b89060', marginBottom: 5, letterSpacing: '0.1em', textTransform: 'uppercase' }}>{lbl}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button onClick={() => set(Math.max(min, val - 1))} style={btnStyle('#fff8ee', '#3b2a14', '#c8a870', '3px 10px')}>−</button>
            <span style={{ minWidth: 22, textAlign: 'center', fontWeight: 'bold', color: '#b45309', fontSize: '1.05rem' }}>{val}</span>
            <button onClick={() => set(Math.min(max, val + 1))} style={btnStyle('#fff8ee', '#3b2a14', '#c8a870', '3px 10px')}>+</button>
          </div>
        </div>
      ))}

      <button onClick={onNew} style={btnStyle('#3b1f08', '#f5ede0', '#8b6340', '8px 20px')}>
        ⚗ Begin Expedition
      </button>

      {gameState === 'running' && <>
        <button onClick={onStep} style={btnStyle('#f0fdf4', '#2e7d32', '#4caf50', '8px 16px')}>
          Step →
        </button>
        <button onClick={onAuto} style={btnStyle(auto ? '#fff0f0' : '#f0f4ff', auto ? '#c62828' : '#1565c0', auto ? '#e53935' : '#6699cc', '8px 16px')}>
          {auto ? '⏸ Pause' : '▶ Auto'}
        </button>
      </>}

      {gameState !== 'setup' && (
        <button onClick={onReveal} style={btnStyle('#faf0ff', '#6a1b9a', '#9c6aaa', '8px 16px')}>
          {reveal ? 'Veil' : '👁 Reveal'}
        </button>
      )}
    </div>
  )
}