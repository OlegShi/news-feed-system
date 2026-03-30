import { useState } from 'react'
import { login } from '../services/api'

export default function Login({ onLogin, onSwitch }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const data = await login(username, password)
      onLogin(data.auth_token)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>News Feed</h2>
      {error && <div className="error-message">{error}</div>}
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <button type="submit">Log In</button>
      <div className="switch-link">
        <a onClick={onSwitch}>Create new account</a>
      </div>
    </form>
  )
}
