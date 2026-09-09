import { useState } from 'react'
import { analyzeAudio } from '../api'
import AiPanel from './AiPanel'
import MetricsGrid from './MetricsGrid'
import ReportView from './ReportView'
import SpectrumView from './SpectrumView'

function UploadPanel({ backendOnline }) {
  const [file, setFile] = useState(null)
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

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
    setReport(null)

    try {
      const payload = await analyzeAudio(file)
      setReport(payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="workspace">
      <aside className="inspector">
        <p className="kicker">INPUT</p>
        <h1>Session</h1>
        <p className="note">
          MP3 or WAV, up to 50 MB. WAV works as-is; MP3 needs ffmpeg. On the public website, use a song under 3 minutes / 15 MB so the server does not time out.
        </p>

        <label className="file-field">
          <input
            type="file"
            accept=".mp3,.wav,audio/mpeg,audio/wav"
            disabled={busy}
            onChange={(event) => {
              setFile(event.target.files[0] || null)
              setReport(null)
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
          {busy ? 'Analyzing…' : 'Analyze'}
        </button>

        {busy && (
          <p className="progress" role="status">
            Measuring loudness, tempo, key, and spectrum…
          </p>
        )}

        {error && (
          <p className="error-box" role="alert">
            {error}
          </p>
        )}
      </aside>

      <section className="report-stage">
        {!report && !busy && (
          <div className="empty">
            <p className="kicker">EMPTY</p>
            <p>Run analysis to generate a session report.</p>
          </div>
        )}

        {busy && (
          <div className="empty">
            <p className="kicker">PROCESSING</p>
            <p>Building report from audio measurements.</p>
          </div>
        )}

        {report && (
          <>
            <ReportView report={report} />
            <MetricsGrid metrics={report.metrics} />
            <AiPanel ai={report.ai} />
            <SpectrumView spectrum={report.spectrum} />
          </>
        )}
      </section>
    </div>
  )
}

export default UploadPanel