import { useState } from 'react'
import { searchLibraryScene } from '../../api'

function chipList(values) {
  return (values || []).filter(Boolean)
}

function SceneSearch({ backendOnline, labels, onPlay }) {
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  async function handleFind(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const payload = await searchLibraryScene(text)
      setResult(payload)
    } catch (err) {
      setError(err.message)
      setResult(null)
    } finally {
      setBusy(false)
    }
  }

  const query = result?.query || {}

  return (
    <div className="scene-search">
      <p className="kicker">FIND MUSIC FOR YOUR SCENE</p>
      <form className="scene-form" onSubmit={handleFind}>
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          disabled={busy || !backendOnline}
          placeholder="Describe your scene… 女主发现男主背叛后，一个人坐在雨夜的出租车里"
          rows={3}
        />
        <button className="action" type="submit" disabled={busy || !backendOnline}>
          {busy ? 'Finding…' : 'Find Music'}
        </button>
      </form>
      {error && (
        <p className="error-box" role="alert">
          {error}
        </p>
      )}
      {result && (
        <>
          <p className="kicker">AI UNDERSTANDS</p>
          <p className="note">
            Mood {(query.mood || []).join(' · ') || '—'}
            <br />
            Scene {(query.scene || []).join(' · ') || '—'}
            <br />
            Relationship {(query.relationship || []).join(' · ') || '—'}
            <br />
            Drama {(query.drama_function || []).join(' · ') || '—'}
            <br />
            Energy {query.energy || '—'} · Tempo{' '}
            {query.tempo_range ? `${query.tempo_range[0]}–${query.tempo_range[1]} BPM` : query.tempo_feel || '—'}
          </p>
          {result.message && <p className="note">{result.message}</p>}
          <p className="kicker">{result.heading}</p>
          {result.matches.length === 0 ? (
            <p className="note">No tracks in the library yet.</p>
          ) : (
            <ul className="match-list">
              {result.matches.map((item, index) => (
                <li className="match-card" key={item.track.id}>
                  <div className="match-head">
                    <strong>
                      {index + 1}. {item.track.title}
                    </strong>
                    <span className="match-score">{Math.round(item.overall)}% Match</span>
                  </div>
                  <p className="note">
                    {item.track.bpm != null ? `${item.track.bpm} BPM` : ''}
                    {item.track.key ? ` · ${item.track.key}` : ''}
                    {item.track.genre ? ` · ${item.track.genre}` : ''}
                    {item.mix_overall != null ? ` · Mix ${item.mix_overall}/100` : ''}
                  </p>
                  <span className="tag-row">
                    {chipList([
                      ...(item.track.tags.mood || []),
                      ...(item.track.tags.scene || []),
                      ...(item.track.tags.relationship || []),
                    ])
                      .slice(0, 6)
                      .map((tag) => (
                        <span className="tag-chip" key={tag}>
                          {labels[tag] || tag}
                        </span>
                      ))}
                  </span>
                  <p className="why-track">
                    <span className="filter-label">Why this track?</span>
                    {item.reason}
                  </p>
                  {item.track.audio_path && (
                    <button
                      type="button"
                      className="text-button tag-button"
                      onClick={() => onPlay(item.track.id)}
                    >
                      Play
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  )
}

export default SceneSearch
