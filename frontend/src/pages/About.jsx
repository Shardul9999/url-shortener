function About() {
  return (
    <>
      <div className="page-header">
        <h1>About this project</h1>
        <p>
          A production-style REST API that shortens URLs, serves cached redirects, and tracks
          click analytics — built to demonstrate async backend patterns end to end.
        </p>
      </div>

      <div className="card">
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>Stack</h2>
        <div className="badge-row">
          <span className="badge">FastAPI</span>
          <span className="badge">PostgreSQL</span>
          <span className="badge">Redis</span>
          <span className="badge">Docker</span>
          <span className="badge">pytest</span>
          <span className="badge">React</span>
          <span className="badge">GitHub Actions</span>
        </div>
      </div>

      <div className="card">
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>What it does</h2>
        <ul className="feature-list">
          <li>
            <strong>Redis cache-aside</strong> on redirects — 6× latency reduction over a
            Postgres round-trip
          </li>
          <li>
            <strong>Sliding-window rate limiting</strong> via Redis atomic pipelines, applied
            independently to shorten and redirect endpoints
          </li>
          <li>
            <strong>SSRF-hardened validation</strong> — rejects private IP ranges, loopback
            addresses, the cloud metadata endpoint, and non-HTTP(S) schemes
          </li>
          <li>
            <strong>Async click tracking</strong> via background tasks — analytics writes never
            block the redirect response
          </li>
          <li>
            <strong>22-test pytest suite</strong> with 87%+ coverage, running on GitHub Actions
            for every push
          </li>
        </ul>
      </div>

      <div className="link-row">
        <a href="https://github.com/Shardul9999/url-shortener" target="_blank" rel="noopener noreferrer">
          GitHub Repo
        </a>
        <a href="https://url-shortener-672q.onrender.com/docs" target="_blank" rel="noopener noreferrer">
          Live API Docs
        </a>
      </div>
    </>
  )
}

export default About
