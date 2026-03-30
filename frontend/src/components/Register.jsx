import { useState } from 'react'
import { register } from '../services/api'

export default function Register({ onRegister, onSwitch }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    try {
      await register(username, password)
      setSuccess('Account created! You can now log in.')
      setTimeout(() => onRegister(), 1500)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>Create Account</h2>
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
      <input
        type="text"
        placeholder="Username (min 3 characters)"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
        minLength={3}
      />
      <input
        type="password"
        placeholder="Password (min 6 characters)"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        minLength={6}
      />
      <button type="submit">Sign Up</button>
      <div className="switch-link">
        <a onClick={onSwitch}>Already have an account?</a>
      </div>
    </form>
  )
}
