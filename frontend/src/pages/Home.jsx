import { useEffect, useRef, useState } from 'react'
import { shortenUrl } from '../api'
import Alert from '../components/Alert'

function classifySecurityMessage(message) {
  return /private|internal|localhost|loopback/i.test(message)
}

function CopyButton({ value }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // clipboard permission denied — silently ignore, link is still selectable
    }
  }

  return (
    <button type="button" className="btn btn-secondary" onClick={handleCopy}>
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function Home() {
  const [originalUrl, setOriginalUrl] = useState('')
  const [expiresInHours, setExpiresInHours] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [retrySeconds, setRetrySeconds] = useState(0)
  const timerRef = useRef(null)

  useEffect(() => {
    return () => clearInterval(timerRef.current)
  }, [])

  function startRetryCountdown(seconds) {
    setRetrySeconds(seconds)
    clearInterval(timerRef.current)
    timerRef.current = setInterval(() => {
      setRetrySeconds((s) => {
        if (s <= 1) {
          clearInterval(timerRef.current)
          return 0
        }
        return s - 1
      })
    }, 1000)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!originalUrl.trim()) return

    setStatus('loading')
    setError(null)

    try {
      const data = await shortenUrl({
        originalUrl: originalUrl.trim(),
        expiresInHours: expiresInHours ? Number(expiresInHours) : null,
      })
      setResult(data)
      setStatus('success')
    } catch (err) {
      setError(err)
      setStatus('error')
      if (err.status === 429) {
        startRetryCountdown(Number(err.retryAfter) || 60)
      }
    }
  }

  const isRateLimited = retrySeconds > 0

  return (
    <>
      <div className="page-header">
        <h1>Shorten a URL</h1>
        <p>Paste a long URL. Get back a fixed-width code that redirects to it.</p>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="original-url">URL to shorten</label>
          <input
            id="original-url"
            type="text"
            className="mono-input data"
            placeholder="https://example.com/some/very/long/path?with=query&params=here"
            value={originalUrl}
            onChange={(e) => setOriginalUrl(e.target.value)}
            disabled={status === 'loading'}
            autoComplete="off"
            spellCheck="false"
          />
        </div>

        <div className="form-row">
          <div className="field">
            <label htmlFor="expires-in">Expires in (hours, optional)</label>
            <input
              id="expires-in"
              type="number"
              min="1"
              placeholder="Never"
              value={expiresInHours}
              onChange={(e) => setExpiresInHours(e.target.value)}
              disabled={status === 'loading'}
            />
          </div>
          <button
            type="submit"
            className="btn"
            disabled={status === 'loading' || !originalUrl.trim() || isRateLimited}
            style={{ marginTop: 22 }}
          >
            {status === 'loading'
              ? 'Compressing…'
              : isRateLimited
                ? `Wait ${retrySeconds}s`
                : 'Shorten'}
          </button>
        </div>
      </form>

      {status === 'success' && result && (
        <div className="result card">
          <div className="result-code-row">
            <span className="result-code">{result.short_code}</span>
            <CopyButton value={result.short_url} />
          </div>
          <div className="result-original">
            <a href={result.short_url} target="_blank" rel="noopener noreferrer" className="data">
              {result.short_url}
            </a>
            {' → '}
            <span className="data">{result.original_url}</span>
          </div>
        </div>
      )}

      {status === 'error' && error && (
        <Alert
          variant={
            error.status === 429
              ? 'ratelimit'
              : error.status === 0
                ? 'generic'
                : classifySecurityMessage(error.message)
                  ? 'security'
                  : 'format'
          }
        >
          {error.status === 429
            ? `Too many requests from your IP. Try again in ${retrySeconds}s.`
            : error.message}
        </Alert>
      )}
    </>
  )
}

export default Home
