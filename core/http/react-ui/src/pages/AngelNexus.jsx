import { useEffect, useMemo, useState } from 'react'
import PageHeader from '../components/PageHeader'

const NEXUS_API = (import.meta.env.VITE_NEXUS_API_URL || '/api/angel-nexus').replace(/\/$/, '')
const REQUEST_TIMEOUT_MS = 10000

async function nexusFetch(path, options = {}) {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  try {
    return await fetch(`${NEXUS_API}${path}`, {
      ...options,
      signal: controller.signal,
      headers: { Accept: 'application/json', ...(options.headers || {}) },
    })
  } catch (error) {
    if (error.name === 'AbortError') throw new Error(`Request timed out after ${REQUEST_TIMEOUT_MS / 1000}s`)
    throw new Error(`Cannot reach Angel Nexus service at ${NEXUS_API}. Start the service or set VITE_NEXUS_API_URL. (${error.message})`)
  } finally {
    window.clearTimeout(timeout)
  }
}

async function readJson(response) {
  const text = await response.text()
  let data = {}
  try { data = text ? JSON.parse(text) : {} } catch { data = { error: text || 'Invalid server response' } }
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`)
  return data
}

export default function AngelNexus() {
  const [modules, setModules] = useState([])
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  const [selected, setSelected] = useState(null)
  const [details, setDetails] = useState(null)
  const [busyId, setBusyId] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [showAdd, setShowAdd] = useState(false)
  const [repoUrl, setRepoUrl] = useState('')
  const [adding, setAdding] = useState(false)

  const loadModules = async () => {
    setError('')
    try {
      const response = await nexusFetch('/api/modules')
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data = await readJson(response)
      setModules(Array.isArray(data.modules) ? data.modules : [])
    } catch (err) {
      setError(`Nexus service unavailable: ${err.message}`)
    }
  }

  useEffect(() => {
    loadModules()
  }, [])

  const categories = useMemo(
    () => ['All', ...new Set(modules.map((module) => module.category).filter(Boolean))],
    [modules]
  )

  const visibleModules = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    return modules.filter((module) => {
      const matchesCategory = category === 'All' || module.category === category
      const haystack = `${module.name} ${module.repo} ${module.description}`.toLowerCase()
      return matchesCategory && (!normalized || haystack.includes(normalized))
    })
  }, [modules, query, category])

  const inspectModule = async (module) => {
    setSelected(module)
    setDetails(null)
    setError('')
    try {
      const response = await nexusFetch(`/api/modules/${encodeURIComponent(module.id)}`)
      const data = await readJson(response)
      setDetails(data)
    } catch (err) {
      setError(`Inspection failed: ${err.message}`)
    }
  }

  const installModule = async (module) => {
    setBusyId(module.id)
    setMessage('')
    setError('')
    try {
      const response = await nexusFetch('/api/modules/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: module.id }),
      })
      const data = await readJson(response)
      setMessage(data.message || 'Module installed.')
      await loadModules()
      await inspectModule({ ...module, installed: true })
    } catch (err) {
      setError(`Install failed: ${err.message}`)
    } finally {
      setBusyId('')
    }
  }

  const addRepository = async (event) => {
    event.preventDefault()
    if (!repoUrl.trim()) return

    setAdding(true)
    setMessage('')
    setError('')
    try {
      const response = await nexusFetch('/api/modules/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl.trim() }),
      })
      const data = await readJson(response)
      setMessage(data.message || 'Repository added.')
      setRepoUrl('')
      setShowAdd(false)
      await loadModules()
    } catch (err) {
      setError(`Add failed: ${err.message}`)
    } finally {
      setAdding(false)
    }
  }

  return (
    <div className="page page--wide">
      <PageHeader
        eyebrow="Angel Nexus"
        title="Module Library"
        supporting="Your maintained TCDOVERLORD tools"
      />

      <div className="form-row">
        <input
          className="input"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search your modules..."
          aria-label="Search your modules"
        />
        <select
          className="input"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          aria-label="Filter by category"
        >
          {categories.map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
          + Add GitHub Module
        </button>
        <button className="btn btn-secondary" onClick={loadModules}>
          Refresh Catalog
        </button>
      </div>

      {message && <div className="card card--accent"><strong>{message}</strong></div>}
      {error && (
        <div className="card">
          <strong>{error}</strong>
          <p className="page-subtitle">Endpoint: {NEXUS_API}. Check that the Angel Nexus service is running and reachable.</p>
        </div>
      )}

      <div className="card-grid">
        {visibleModules.map((module) => (
          <section className="card" key={module.id}>
            <div className="section-heading">
              <i className="fas fa-cubes" aria-hidden="true" /> {module.name}
            </div>
            <p className="page-subtitle">{module.description || 'GitHub module'}</p>
            <p><strong>Category:</strong> {module.category || 'Custom'}</p>
            <p><strong>Repository:</strong> {module.repo}</p>
            <p>
              <strong>Status:</strong>{' '}
              <span>{module.installed ? 'Installed' : 'Not installed'}</span>
            </p>
            <div className="form-row">
              <button className="btn btn-secondary" onClick={() => inspectModule(module)}>
                Inspect Module
              </button>
              <a
                className="btn btn-secondary"
                href={`https://github.com/${module.repo}`}
                target="_blank"
                rel="noreferrer"
              >
                GitHub
              </a>
              <button
                className="btn btn-primary"
                disabled={busyId === module.id}
                onClick={() => installModule(module)}
              >
                {busyId === module.id ? 'Installing...' : module.installed ? 'Update' : 'Install'}
              </button>
            </div>
          </section>
        ))}
      </div>

      {!visibleModules.length && (
        <div className="card">
          <strong>No modules match your search.</strong>
        </div>
      )}

      {showAdd && (
        <div className="card card--accent">
          <div className="section-heading">Add GitHub Module</div>
          <p className="page-subtitle">
            Paste a public GitHub HTTPS repository URL. The repository is added to the catalog first;
            installation happens separately.
          </p>
          <form onSubmit={addRepository}>
            <div className="form-row">
              <input
                className="input"
                value={repoUrl}
                onChange={(event) => setRepoUrl(event.target.value)}
                placeholder="https://github.com/owner/repository.git"
                required
              />
              <button className="btn btn-primary" type="submit" disabled={adding}>
                {adding ? 'Adding...' : 'Add Repository'}
              </button>
              <button className="btn btn-secondary" type="button" onClick={() => setShowAdd(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {selected && (
        <div className="card card--accent">
          <div className="section-heading">
            <i className="fas fa-folder-open" aria-hidden="true" /> {selected.name}
          </div>
          {!details && <p className="page-subtitle">Loading module details...</p>}
          {details && (
            <>
              <p><strong>Project type:</strong> {details.project_type}</p>
              <p><strong>Local path:</strong> {details.module.installed_path || 'Not installed'}</p>
              <p><strong>Preview:</strong> {details.preview_url || 'Not available'}</p>

              <h3>README.md</h3>
              <pre style={{ whiteSpace: 'pre-wrap', overflowX: 'auto' }}>
                {details.readme || 'No README.md found.'}
              </pre>

              <h3>Files</h3>
              <pre style={{ whiteSpace: 'pre-wrap', overflowX: 'auto' }}>
                {(details.files || []).join('\n') || 'No files listed.'}
              </pre>

              {details.preview_url && (
                <a
                  className="btn btn-primary"
                  href={`${NEXUS_API}${details.preview_url}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Launch Preview
                </a>
              )}

              <button className="btn btn-secondary" onClick={() => {
                setSelected(null)
                setDetails(null)
              }}>
                Close Details
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}
