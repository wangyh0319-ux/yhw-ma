import { useState } from 'react'
import { mixAudio } from '../../api'
import MixCharts from './MixCharts'
import MixIssueList from './MixIssueList'
import MixReportView from './MixReportView'
import MixScoreBoard from './MixScoreBoard'

function MixingWorkspace({ backendOnline }) {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [showReport, setShowReport] = useState(false)

  async function handleAnalyze() {
    if (!backendOnline) {
      setError('Backend is offline.')
      return
    }
    if (!file) {
      setError('Choose an MP3 or WAV file first.')
      return
    }

    setBusy(true)
    setError('')
    setResult(null)
    setShowReport(false)

    try {
      const payload = await mixAudio(file)
      setResult(payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="workspace">
      <aside className="inspector">
        <p className="kicker">MIXING ASSISTANT</p>
        <h1>Upload mix</h1>
        <p className="note">WAV or MP3 of a bounced mix. DSP scores first; AI only interprets those numbers.</p>

        <label className="file-field">
          <input
            type="file"
            accept=".mp3,.wav,audio/mpeg,audio/wav"
            disabled={busy}
            onChange={(event) => {
              setFile(event.target.files[0] || null)
              setResult(null)
              setShowReport(false)
              setError('')
            }}
          />
          <span>{file ? file.name : 'Choose file'}</span>
        </label>

        <button
          type="button"
          className="action"
          disabled={busy || !backendOnline}
          onClick={handleAnalyze}
        >
          {busy ? 'Analyzing…' : 'Analyze mix'}
        </button>

        {result && (
          <button
            type="button"
            className="action secondary"
            onClick={() => setShowReport(true)}
          >
            Generate report
          </button>
        )}

        {busy && (
          <p className="progress" role="status">
            Measuring loudness, frequency, dynamics, stereo, and peaks…
          </p>
        )}

        {error && (
          <p className="error-box" role="alert">
            {error}
          </p>
        )}
      </aside>

      <section className="report-stage">
        {!result && !busy && (
          <div className="empty">
            <p className="kicker">EMPTY</p>
            <p>Upload a mix to see Mix Health, issues, and charts.</p>
          </div>
        )}

        {busy && (
          <div className="empty">
            <p className="kicker">PROCESSING</p>
            <p>Building mix measurements. AI text comes after you generate the report.</p>
          </div>
        )}

        {result && (
          <>
            <header className="report-head">
              <p className="kicker">SESSION</p>
              <h2>{result.file.filename}</h2>
            </header>
            <MixScoreBoard scores={result.scores} />
            <MixIssueList scores={result.scores} />
            <MixCharts result={result} />
            {showReport && <MixReportView report={result.ai_report} />}
          </>
        )}
      </section>
    </div>
  )
}

export default MixingWorkspace