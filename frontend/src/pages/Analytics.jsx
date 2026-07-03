import { useState } from 'react'
import { getAnalytics } from '../api'
import Alert from '../components/Alert'

function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function StatSkeleton() {
  return (
    <div className="stat-grid" aria-hidden="true">
      <div className="stat">
        <div className="stat-label">Total clicks</div>
        <div className="skeleton" style={{ height: 26, width: 48, marginTop: 4 }} />
      </div>
      <div className="stat">
        <div className="stat-label">Created</div>
        <div className="skeleton" style={{ height: 26, width: 90, marginTop: 4 }} />
      </div>
      <div className="stat">
        <div className="stat-label">Expires</div>
        <div className="skeleton" style={{ height: 26, width: 70, marginTop: 4 }} />
      </div>
    </div>
  )
}

function Analytics() {
  const [shortCode, setShortCode] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  async function handleSubmit(event) {
    event.preventDefault()
    const code = shortCode.trim()
    if (!code) return

    setStatus('loading')
    setError(null)

    try {
      const result = await getAnalytics(code)
      setData(result)
      setStatus('success')
    } catch (err) {
      setError(err)
      setStatus('error')
    }
  }

  return (
    <>
      <div className="page-header">
        <h1>Look up analytics</h1>
        <p>Enter a short code to see click count, expiry, and recent activity.</p>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <div className="form-row">
          <div className="field">
            <label htmlFor="lookup-code">Short code</label>
            <input
              id="lookup-code"
              type="text"
              className="mono-input data"
              placeholder="a1B2c3"
              value={shortCode}
              onChange={(e) => setShortCode(e.target.value)}
              disabled={status === 'loading'}
              autoComplete="off"
              spellCheck="false"
            />
          </div>
          <button
            type="submit"
            className="btn"
            disabled={status === 'loading' || !shortCode.trim()}
            style={{ marginTop: 22 }}
          >
            {status === 'loading' ? 'Looking up…' : 'Look up'}
          </button>
        </div>
      </form>

      {status === 'loading' && <StatSkeleton />}

      {status === 'error' && error && (
        <Alert variant={error.status === 404 ? 'notfound' : 'generic'}>
          {error.status === 404 ? (
            <>
              No analytics found for <code>{shortCode.trim()}</code>. Check the code and try
              again.
            </>
          ) : (
            error.message
          )}
        </Alert>
      )}

      {status === 'success' && data && (
        <>
          <div className="stat-grid">
            <div className="stat">
              <div className="stat-label">Total clicks</div>
              <div className="stat-value">{data.click_count}</div>
            </div>
            <div className="stat">
              <div className="stat-label">Created</div>
              <div className="stat-value" style={{ fontSize: 15 }}>
                {formatDate(data.created_at)}
              </div>
            </div>
            <div className="stat">
              <div className="stat-label">Expires</div>
              <div className="stat-value" style={{ fontSize: 15 }}>
                {data.expires_at ? formatDate(data.expires_at) : 'Never'}
              </div>
            </div>
          </div>

          <div className="result-original" style={{ marginBottom: 20 }}>
            Original URL: <span className="data">{data.original_url}</span>
          </div>

          <div className="card">
            {data.recent_clicks.length === 0 ? (
              <div className="empty-state">No clicks recorded yet.</div>
            ) : (
              <div className="table-scroll">
              <table className="click-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Referrer</th>
                    <th>IP</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_clicks.map((click, i) => (
                    <tr key={i}>
                      <td className="data">{formatDate(click.clicked_at)}</td>
                      <td className="data">{click.referrer || '—'}</td>
                      <td className="data">{click.ip_address || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>
            )}
          </div>
        </>
      )}
    </>
  )
}

export default Analytics
