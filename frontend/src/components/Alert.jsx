const ICONS = {
  security: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 2 4 5v6c0 5 3.5 9 8 11 4.5-2 8-6 8-11V5l-8-3Z" />
      <path d="M12 8v5" strokeLinecap="round" />
      <circle cx="12" cy="16" r="0.5" fill="currentColor" />
    </svg>
  ),
  ratelimit: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  notfound: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" strokeLinecap="round" />
    </svg>
  ),
  format: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v5" strokeLinecap="round" />
      <circle cx="12" cy="16" r="0.5" fill="currentColor" />
    </svg>
  ),
  generic: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v5" strokeLinecap="round" />
      <circle cx="12" cy="16" r="0.5" fill="currentColor" />
    </svg>
  ),
}

const TITLES = {
  security: 'Blocked for security',
  ratelimit: 'Rate limit reached',
  notfound: 'Not found',
  format: 'Invalid URL',
  generic: 'Error',
}

function Alert({ variant = 'generic', title, children }) {
  return (
    <div className={`alert alert--${variant}`} role="alert">
      <span className="alert-icon" aria-hidden="true">
        {ICONS[variant]}
      </span>
      <div>
        <div className="alert-title">{title || TITLES[variant]}</div>
        <div className="alert-body">{children}</div>
      </div>
    </div>
  )
}

export default Alert
