function MixReportView({ report }) {
  if (!report?.available) {
    return (
      <section className="panel">
        <p className="kicker">AI MIXING REPORT</p>
        <p className="note">{report?.message || 'AI report is unavailable.'}</p>
      </section>
    )
  }

  const sections = [
    ['Overall Assessment', report.overall_assessment],
    ['Frequency Balance', report.frequency_balance],
    ['Dynamics', report.dynamics],
    ['Loudness', report.loudness],
    ['Stereo Image', report.stereo_image],
    ['Clipping / Peak', report.clipping_peak],
  ]

  return (
    <section className="panel">
      <p className="kicker">AI MIXING REPORT</p>
      {sections.map(([title, text]) => (
        <div className="report-block" key={title}>
          <h3 className="chart-title">{title}</h3>
          <p className="note">{text || '—'}</p>
        </div>
      ))}

      <h3 className="chart-title">Priority Issues</h3>
      <ul className="report-list">
        {(report.priority_issues || []).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h3 className="chart-title">Suggested Actions</h3>
      <ul className="report-list">
        {(report.suggested_actions || []).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h3 className="chart-title">What Already Works</h3>
      <ul className="report-list">
        {(report.what_already_works || []).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  )
}

export default MixReportView