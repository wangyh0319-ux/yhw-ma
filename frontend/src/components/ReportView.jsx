function ReportView({ report }) {
  return (
    <article className="report">
      <header className="report-head">
        <p className="kicker">REPORT</p>
        <h2>{report.file.filename}</h2>
        <p className="summary">{report.summary}</p>
      </header>
    </article>
  )
}

export default ReportView