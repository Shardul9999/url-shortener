import { NavLink, Outlet } from 'react-router-dom'

function Layout() {
  return (
    <div className="shell">
      <header className="header">
        <NavLink to="/" className="wordmark">
          url<span>/</span>shortener
        </NavLink>
        <ul className="nav">
          <li>
            <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
              Shorten
            </NavLink>
          </li>
          <li>
            <NavLink to="/analytics" className={({ isActive }) => (isActive ? 'active' : '')}>
              Analytics
            </NavLink>
          </li>
          <li>
            <NavLink to="/about" className={({ isActive }) => (isActive ? 'active' : '')}>
              About
            </NavLink>
          </li>
        </ul>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="footer">
        <span>URL Shortener &amp; Analytics API</span>
        <a href="https://github.com/Shardul9999/url-shortener" target="_blank" rel="noopener noreferrer">
          GitHub
        </a>
      </footer>
    </div>
  )
}

export default Layout
