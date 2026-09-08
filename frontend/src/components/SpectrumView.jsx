function SpectrumView({ spectrum }) {
  const values = spectrum.bars.map((bar) => bar.db)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1

  return (
    <section className="panel">
      <p className="kicker">SPECTRUM</p>
      <div className="spectrum" aria-label="Spectrum bars">
        {spectrum.bars.map((bar, index) => {
          const height = ((bar.db - min) / span) * 100
          return (
            <span
              key={`${bar.hz}-${index}`}
              className="spectrum-bar"
              style={{ height: `${Math.max(height, 4)}%` }}
              title={`${bar.hz} Hz · ${bar.db} dB`}
            />
          )
        })}
      </div>
      <div className="spectrum-axis">
        <span>Low</span>
        <span>High</span>
      </div>
      <dl className="bands">
        {Object.entries(spectrum.bands).map(([name, db]) => (
          <div key={name}>
            <dt>{name.replaceAll('_', ' ')}</dt>
            <dd>{db.toFixed(1)} dB</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

export default SpectrumView