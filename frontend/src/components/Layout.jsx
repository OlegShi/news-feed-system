export default function Layout({ user, onLogout, children }) {
  return (
    <div className="layout">
      <nav className="navbar">
        <h1>News Feed</h1>
        <div className="user-info">
          <span>{user?.username}</span>
          <button onClick={onLogout}>Log Out</button>
        </div>
      </nav>
      {children}
    </div>
  )
}
