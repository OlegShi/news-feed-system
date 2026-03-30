import { useState, useEffect } from 'react'
import Login from './components/Login'
import Register from './components/Register'
import NewsFeed from './components/NewsFeed'
import PostForm from './components/PostForm'
import FriendsList from './components/FriendsList'
import Layout from './components/Layout'

function App() {
  const [token, setToken] = useState(localStorage.getItem('auth_token') || '')
  const [user, setUser] = useState(null)
  const [view, setView] = useState('login')
  const [refreshFeed, setRefreshFeed] = useState(0)

  useEffect(() => {
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        setUser({ user_id: payload.user_id, username: payload.username })
        setView('feed')
      } catch {
        setToken('')
        localStorage.removeItem('auth_token')
      }
    }
  }, [token])

  const handleLogin = (authToken) => {
    setToken(authToken)
    localStorage.setItem('auth_token', authToken)
  }

  const handleLogout = () => {
    setToken('')
    setUser(null)
    localStorage.removeItem('auth_token')
    setView('login')
  }

  const handlePostCreated = () => {
    setRefreshFeed((prev) => prev + 1)
  }

  if (!token || view === 'login' || view === 'register') {
    return (
      <div className="auth-container">
        {view === 'register' ? (
          <Register onRegister={() => setView('login')} onSwitch={() => setView('login')} />
        ) : (
          <Login onLogin={handleLogin} onSwitch={() => setView('register')} />
        )}
      </div>
    )
  }

  return (
    <Layout user={user} onLogout={handleLogout}>
      <div className="main-content">
        <div className="feed-column">
          <PostForm token={token} onPostCreated={handlePostCreated} />
          <NewsFeed token={token} refreshTrigger={refreshFeed} />
        </div>
        <div className="sidebar">
          <FriendsList token={token} />
        </div>
      </div>
    </Layout>
  )
}

export default App
