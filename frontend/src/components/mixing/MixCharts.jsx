function MiniBars({ values, unit }) {
  const numbers = values.map((item) => item.value).filter((value) => value !== null)
  const min = numbers.length ? Math.min(...numbers) : 0
  const max = numbers.length ? Math.max(...numbers) : 1
  const span = max - min || 1

  return (
    <div className="spectrum mix-bars">
      {values.map((item) => {
        const height =
          item.value === null ? 8 : ((item.value - min) / span) * 100
        return (
          <span
            key={item.label}
            className="spectrum-bar"
            style={{ height: `${Math.max(height, 8)}%` }}
            title={`${item.label}: ${item.value ?? 'n/a'} ${unit}`}
          />
        )
      })}
    </div>
  )
}

function MixCharts({ result }) {
  const bands = Object.entries(result.frequency.bands).map(([name, data]) => ({
    label: name,
    value: data.relative_to_mid_db,
  }))
  const loudness = [
    { label: 'Integrated', value: result.loudness.integrated_lufs },
    { label: 'Short-term', value: result.loudness.short_term_lufs },
    { label: 'Momentary', value: result.loudness.momentary_lufs },
    { label: 'True Peak', value: result.loudness.true_peak_dbtp },
  ]
  const dynamics = [
    { label: 'Crest dB', value: result.dynamics.crest_factor_db },
    { label: 'DR', value: result.dynamics.dynamic_range_db },
    { label: 'Peak/RMS', value: result.dynamics.peak_to_rms_db },
  ]
  const stereo = result.stereo.available
    ? [
        { label: 'Width', value: result.stereo.width },
        { label: 'Corr', value: result.stereo.correlation },
        { label: 'L/R dB', value: result.stereo.lr_balance_db },
      ]
    : []

  return (
    <section className="panel">
      <p className="kicker">MEASUREMENTS</p>
      <p className="note">These charts are the DSP numbers behind the scores.</p>

      <h3 className="chart-title">Frequency vs Mid</h3>
      <MiniBars values={bands} unit="dB" />

      <h3 className="chart-title">Loudness</h3>
      <MiniBars values={loudness} unit="LUFS / dBTP" />

      <h3 className="chart-title">Dynamics</h3>
      <MiniBars values={dynamics} unit="dB" />

      <h3 className="chart-title">Stereo</h3>
      {stereo.length ? (
        <MiniBars values={stereo} unit="" />
      ) : (
        <p className="note">{result.stereo.message}</p>
      )}
    </section>
  )
}

export default MixCharts