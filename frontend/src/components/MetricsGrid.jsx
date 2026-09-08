function formatDuration(seconds) {
  const total = Math.max(0, Math.round(seconds))
  const minutes = Math.floor(total / 60)
  const rest = String(total % 60).padStart(2, '0')
  return `${minutes}:${rest}`
}

function MetricsGrid({ metrics }) {
  const items = [
    ['BPM', metrics.bpm.toFixed(1)],
    ['Key', metrics.key],
    ['Duration', formatDuration(metrics.duration_sec)],
    ['LUFS', metrics.lufs === null ? '—' : metrics.lufs.toFixed(1)],
    ['RMS', `${metrics.rms_db.toFixed(1)} dB`],
    ['Dyn. Range', `${metrics.dynamic_range_db.toFixed(1)} dB`],
  ]

  return (
    <section className="panel">
      <p className="kicker">METRICS</p>
      <div className="metric-cards">
        {items.map(([label, value]) => (
          <div className="metric-card" key={label}>
            <span className="metric-label">{label}</span>
            <span className="metric-value">{value}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

export default MetricsGrid