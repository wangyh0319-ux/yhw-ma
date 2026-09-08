import { useEffect, useState } from 'react'
import { checkHealth } from './api'
import UploadPanel from './components/UploadPanel'
import MixingWorkspace from './components/mixing/MixingWorkspace'
import LibraryWorkspace from './components/library/LibraryWorkspace'

function App() {
  const [backend, setBackend] = useState('checking')
  const [mode, setMode] = useState('analyze')

  useEffect(() => {
    checkHealth()
      .then((data) => {
        setBackend(data.ok ? 'connected' : 'offline')
      })
      .catch(() => {
        setBackend('offline')
      })
  }, [])

  return (
    <div className="shell">
      <header className="topbar">
        <div className="topbar-left">
          <span className="brand">AI Music Analyzer</span>
          <nav className="mode-nav" aria-label="Modules">
            <button
              type="button"
              className={mode === 'analyze' ? 'active' : ''}
              onClick={() => setMode('analyze')}
            >
              Analyzer
            </button>
            <button
              type="button"
              className={mode === 'mixing' ? 'active' : ''}
              onClick={() => setMode('mixing')}
            >
              Mixing Assistant
            </button>
            <button
              type="button"
              className={mode === 'library' ? 'active' : ''}
              onClick={() => setMode('library')}
            >
              Library
            </button>
          </nav>
        </div>
        <span className={`status ${backend}`}>
          {backend === 'checking' && 'CHECKING BACKEND'}
          {backend === 'connected' && 'BACKEND CONNECTED'}
          {backend === 'offline' && 'BACKEND OFFLINE'}
        </span>
      </header>
      {mode === 'analyze' && (
        <UploadPanel backendOnline={backend === 'connected'} />
      )}
      {mode === 'mixing' && (
        <MixingWorkspace backendOnline={backend === 'connected'} />
      )}
      {mode === 'library' && (
        <LibraryWorkspace backendOnline={backend === 'connected'} />
      )}
    </div>
  )
}

export default App