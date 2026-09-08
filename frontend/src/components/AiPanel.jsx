function AiPanel({ ai }) {
  if (!ai?.available) {
    return (
      <section className="panel">
        <p className="kicker">AI</p>
        <p className="note">{ai?.message || 'AI labels are unavailable.'}</p>
      </section>
    )
  }

  const items = [
    ['Genre', ai.genre || '—'],
    ['Mood', ai.mood || '—'],
    ['Energy', ai.energy_label ? `${ai.energy_label} · ${ai.energy}` : String(ai.energy ?? '—')],
  ]

  return (
    <section className="panel">
      <p className="kicker">AI</p>
      <div className="metric-cards">
        {items.map(([label, value]) => (
          <div className="metric-card" key={label}>
            <span className="metric-label">{label}</span>
            <span className="metric-value">{value}</span>
          </div>
        ))}
      </div>
      {ai.reason && <p className="note">{ai.reason}</p>}
    </section>
  )
}

export default AiPanel