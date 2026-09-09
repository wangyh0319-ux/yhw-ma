import { useEffect, useMemo, useState } from 'react'
import SceneSearch from './SceneSearch'
import {
  createLibraryTrack,
  deleteLibraryTrack,
  libraryAudioUrl,
  listLibraryTaxonomy,
  listLibraryTracks,
  tagLibraryTrack,
  uploadLibraryTrack,
} from '../../api'

function formatDuration(seconds) {
  if (seconds === null || seconds === undefined) {
    return ''
  }
  const total = Math.max(0, Math.round(seconds))
  const minutes = Math.floor(total / 60)
  const rest = String(total % 60).padStart(2, '0')
  return `${minutes}:${rest}`
}

function toggleValue(list, value) {
  if (list.includes(value)) {
    return list.filter((item) => item !== value)
  }
  return [...list, value]
}

function trackMoods(track) {
  return track.tags?.mood || []
}

function trackStyles(track) {
  const fromTags = track.tags?.style || []
  if (track.genre && !fromTags.includes(track.genre)) {
    return [track.genre, ...fromTags]
  }
  return fromTags
}

function trackTagList(track, namespace) {
  return track.tags?.[namespace] || []
}

function FilterRow({ title, items, selected, onToggle }) {
  if (!items || items.length === 0) {
    return null
  }
  return (
    <>
      <p className="filter-label">{title}</p>
      <div className="filter-row">
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`filter-chip${selected.includes(item.id) ? ' is-on' : ''}`}
            onClick={() => onToggle(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
    </>
  )
}

function LibraryWorkspace({ backendOnline }) {
  const [tracks, setTracks] = useState([])
  const [taxonomy, setTaxonomy] = useState({
    mood: [],
    style: [],
    scene: [],
    relationship: [],
    drama_function: [],
  })
  const [title, setTitle] = useState('')
  const [artist, setArtist] = useState('')
  const [files, setFiles] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [moods, setMoods] = useState([])
  const [styles, setStyles] = useState([])
  const [scenes, setScenes] = useState([])
  const [relationships, setRelationships] = useState([])
  const [functions, setFunctions] = useState([])
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState('')
  const [pickerKey, setPickerKey] = useState(0)

  const labels = useMemo(() => {
    const map = {}
    for (const group of [
      taxonomy.mood,
      taxonomy.style,
      taxonomy.scene,
      taxonomy.relationship,
      taxonomy.drama_function,
    ]) {
      for (const item of group || []) {
        map[item.id] = item.label
      }
    }
    return map
  }, [taxonomy])

  function labelFor(id) {
    return labels[id] || id
  }

  async function refresh() {
    const items = await listLibraryTracks()
    setTracks(items)
  }

  useEffect(() => {
    if (!backendOnline) {
      return
    }
    refresh().catch((err) => setError(err.message))
    listLibraryTaxonomy()
      .then(setTaxonomy)
      .catch((err) => setError(err.message))
  }, [backendOnline])

  async function ingestOne(file, trackTitle) {
    const saved = await uploadLibraryTrack(file, trackTitle, artist)
    const tagged = await tagLibraryTrack(saved.id)
    return tagged
  }

  async function handleCreate(event) {
    event.preventDefault()
    if (files.length === 0 && !title.trim()) {
      setError('Choose files or enter a title.')
      return
    }
    setBusy(true)
    setError('')
    setInfo('')
    setProgress('')
    try {
      if (files.length === 0) {
        await createLibraryTrack(title, artist)
        setTitle('')
        setArtist('')
        await refresh()
        return
      }

      const failed = []
      let lastTagMessage = ''
      const total = files.length
      for (let index = 0; index < files.length; index += 1) {
        const file = files[index]
        const trackTitle = files.length === 1 ? title || file.name.replace(/\.[^.]+$/, '') : ''
        setProgress(`Saving ${index + 1} / ${total} · ${file.name}`)
        try {
          const tagged = await ingestOne(file, trackTitle)
          if (tagged.tagging?.message) {
            lastTagMessage = tagged.tagging.message
          }
        } catch (err) {
          failed.push(`${file.name}: ${err.message}`)
        }
        await refresh()
      }

      setFiles([])
      setPickerKey((value) => value + 1)
      setTitle('')
      if (failed.length === 0) {
        setArtist('')
      }
      if (lastTagMessage) {
        setInfo(lastTagMessage)
      }
      if (failed.length > 0) {
        setError(
          `Saved ${total - failed.length} of ${total}. Failed:\n${failed.join('\n')}`,
        )
      } else if (total > 1) {
        setInfo(
          lastTagMessage
            ? `${total} tracks saved. ${lastTagMessage}`
            : `${total} tracks saved and tagged.`,
        )
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
      setProgress('')
    }
  }

  async function handleTag(trackId) {
    setBusy(true)
    setError('')
    setInfo('')
    try {
      const tagged = await tagLibraryTrack(trackId)
      if (tagged.tagging?.message) {
        setInfo(tagged.tagging.message)
      }
      await refresh()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleTagAll() {
    const pending = tracks.filter((track) => track.audio_path)
    if (pending.length === 0) {
      setError('No audio files to tag.')
      return
    }
    setBusy(true)
    setError('')
    setInfo('')
    const failed = []
    try {
      for (let index = 0; index < pending.length; index += 1) {
        const track = pending[index]
        setProgress(`Tagging ${index + 1} / ${pending.length} · ${track.title}`)
        try {
          await tagLibraryTrack(track.id)
        } catch (err) {
          failed.push(`${track.title}: ${err.message}`)
        }
        await refresh()
      }
      if (failed.length > 0) {
        setError(`Tagged with some failures:\n${failed.join('\n')}`)
      } else {
        setInfo('All tracks now have mood and style tags.')
      }
    } finally {
      setBusy(false)
      setProgress('')
    }
  }

  async function handleDelete(trackId) {
    setError('')
    try {
      await deleteLibraryTrack(trackId)
      if (selectedId === trackId) {
        setSelectedId(null)
      }
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  const visible = tracks.filter((track) => {
    const moodOk = moods.length === 0 || moods.some((item) => trackMoods(track).includes(item))
    const styleOk = styles.length === 0 || styles.some((item) => trackStyles(track).includes(item))
    const sceneOk =
      scenes.length === 0 || scenes.some((item) => trackTagList(track, 'scene').includes(item))
    const relOk =
      relationships.length === 0 ||
      relationships.some((item) => trackTagList(track, 'relationship').includes(item))
    const fnOk =
      functions.length === 0 ||
      functions.some((item) => trackTagList(track, 'drama_function').includes(item))
    return moodOk && styleOk && sceneOk && relOk && fnOk
  })
  const selected = tracks.find((track) => track.id === selectedId)

  return (
    <div className="workspace">
      <aside className="inspector">
        <p className="kicker">LIBRARY</p>
        <h1>Short Drama</h1>
        <p className="note">
          一次可选多个 WAV/MP3。系统会打上情绪和风格标签；点标签即可筛选曲库。
        </p>

        <form className="library-form" onSubmit={handleCreate}>
          <label className="file-field">
            <input
              key={pickerKey}
              type="file"
              multiple
              accept=".mp3,.wav,audio/mpeg,audio/wav"
              disabled={busy || !backendOnline}
              onChange={(event) => setFiles(Array.from(event.target.files || []))}
            />
            <span>
              {files.length === 0
                ? 'Choose audio (batch OK)'
                : files.length === 1
                  ? files[0].name
                  : `${files.length} files selected`}
            </span>
          </label>
          {files.length > 1 && (
            <ul className="file-preview">
              {files.slice(0, 8).map((file, index) => (
                <li key={`${file.name}-${file.size}-${index}`}>{file.name}</li>
              ))}
              {files.length > 8 && <li>+{files.length - 8} more</li>}
            </ul>
          )}
          <label>
            Title
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              disabled={busy || !backendOnline || files.length > 1}
              placeholder={files.length > 1 ? 'Using each filename' : 'Optional if you upload a file'}
            />
          </label>
          <label>
            Artist
            <input
              value={artist}
              onChange={(event) => setArtist(event.target.value)}
              disabled={busy || !backendOnline}
              placeholder={files.length > 1 ? 'Applied to every file' : ''}
            />
          </label>
          <button className="action" type="submit" disabled={busy || !backendOnline}>
            {busy
              ? 'Saving…'
              : files.length > 1
                ? `Add ${files.length} tracks`
                : 'Add to library'}
          </button>
        </form>
        <button
          type="button"
          className="text-button tag-button tag-all"
          onClick={handleTagAll}
          disabled={busy || !backendOnline}
        >
          Tag all
        </button>

        {progress && <p className="note">{progress}</p>}
        {info && <p className="note">{info}</p>}
        {error && (
          <p className="error-box" role="alert">
            {error}
          </p>
        )}
      </aside>

      <section className="report-stage">
        <SceneSearch
          backendOnline={backendOnline}
          labels={labels}
          onPlay={setSelectedId}
        />
        {selected?.audio_path && (
          <div className="player-panel">
            <p className="kicker">PLAYER</p>
            <h2>{selected.title}</h2>
            <audio controls src={libraryAudioUrl(selected.id)} />
          </div>
        )}

        <div className="filter-panel">
          <p className="kicker">SEARCH BY TAGS</p>
          <FilterRow
            title="情绪 Mood"
            items={taxonomy.mood}
            selected={moods}
            onToggle={(id) => setMoods((current) => toggleValue(current, id))}
          />
          <FilterRow
            title="场景 Scene"
            items={taxonomy.scene}
            selected={scenes}
            onToggle={(id) => setScenes((current) => toggleValue(current, id))}
          />
          <FilterRow
            title="关系 Relationship"
            items={taxonomy.relationship}
            selected={relationships}
            onToggle={(id) => setRelationships((current) => toggleValue(current, id))}
          />
          <FilterRow
            title="剧情功能 Drama"
            items={taxonomy.drama_function}
            selected={functions}
            onToggle={(id) => setFunctions((current) => toggleValue(current, id))}
          />
          <FilterRow
            title="风格 Style"
            items={taxonomy.style}
            selected={styles}
            onToggle={(id) => setStyles((current) => toggleValue(current, id))}
          />
          {(moods.length > 0 ||
            styles.length > 0 ||
            scenes.length > 0 ||
            relationships.length > 0 ||
            functions.length > 0) && (
            <button
              type="button"
              className="text-button tag-button"
              onClick={() => {
                setMoods([])
                setStyles([])
                setScenes([])
                setRelationships([])
                setFunctions([])
              }}
            >
              Clear filters
            </button>
          )}
        </div>

        <p className="kicker">CATALOG · {visible.length}</p>
        {tracks.length === 0 ? (
          <div className="empty">
            <p>No tracks yet. Upload a mix to start the library.</p>
          </div>
        ) : visible.length === 0 ? (
          <div className="empty">
            <p>No tracks match these mood/style tags.</p>
          </div>
        ) : (
          <ul className="track-list">
            {visible.map((track) => (
              <li className="track-row" key={track.id}>
                <button
                  type="button"
                  className="track-select"
                  onClick={() => setSelectedId(track.id)}
                >
                  <strong>{track.title}</strong>
                  <span className="note">
                    {track.artist || 'Unknown'}
                    {track.bpm != null ? ` · ${track.bpm} BPM` : ''}
                    {track.key ? ` · ${track.key}` : ''}
                    {track.duration_sec != null ? ` · ${formatDuration(track.duration_sec)}` : ''}
                    {track.audio_path ? '' : ' · no audio'}
                  </span>
                  <span className="tag-row">
                    {trackStyles(track).map((tag) => (
                      <span className="tag-chip style-chip" key={`style-${tag}`}>
                        {labelFor(tag)}
                      </span>
                    ))}
                    {trackMoods(track).map((tag) => (
                      <span className="tag-chip" key={`mood-${tag}`}>
                        {labelFor(tag)}
                      </span>
                    ))}
                    {trackTagList(track, 'scene').map((tag) => (
                      <span className="tag-chip" key={`scene-${tag}`}>
                        {labelFor(tag)}
                      </span>
                    ))}
                  </span>
                </button>
                {track.audio_path && (
                  <button
                    type="button"
                    className="text-button tag-button"
                    onClick={() => handleTag(track.id)}
                    disabled={busy}
                  >
                    Analyze & tag
                  </button>
                )}
                <button type="button" className="text-button" onClick={() => handleDelete(track.id)}>
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

export default LibraryWorkspace
