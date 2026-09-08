function scoreLabel(value) {
  return value === null || value === undefined ? '—' : String(value)
}

function MixScoreBoard({ scores }) {
  const items = [
    ['Overall', scores.overall],
    ['Frequency', scores.frequency],
    ['Dynamics', scores.dynamics],
    ['Stereo', scores.stereo],
    ['Loudness', scores.loudness],
  ]

  return (
    <section className="panel">
      <p className="kicker">MIX HEALTH</p>
      <div className="score-cards">
        {items.map(([label, value]) => (
          <div className="metric-card" key={label}>
            <span className="metric-label">{label}</span>
            <span className="metric-value">{scoreLabel(value)}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

export default MixScoreBoard