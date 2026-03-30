import { useState, useEffect } from 'react'
import { getFriends, addFriend } from '../services/api'

export default function FriendsList({ token }) {
  const [friends, setFriends] = useState([])
  const [username, setUsername] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadFriends = async () => {
    try {
      const data = await getFriends(token)
      setFriends(data.friends)
    } catch (err) {
      console.error('Failed to load friends:', err)
    }
  }

  useEffect(() => {
    loadFriends()
  }, [token])

  const handleAdd = async (e) => {
    e.preventDefault()
    if (!username.trim()) return
    setError('')
    setSuccess('')
    try {
      await addFriend(token, username)
      setSuccess(`Added ${username}`)
      setUsername('')
      loadFriends()
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(err.message)
      setTimeout(() => setError(''), 3000)
    }
  }

  return (
    <div className="friends-panel">
      <h3>Friends ({friends.length})</h3>
      <form className="add-friend-form" onSubmit={handleAdd}>
        <input
          type="text"
          placeholder="Add by username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <button type="submit">Add</button>
      </form>
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
      {friends.map((friend) => (
        <div key={friend.user_id} className="friend-item">
          <div className="avatar-small">
            {friend.username[0].toUpperCase()}
          </div>
          <span>{friend.username}</span>
        </div>
      ))}
      {friends.length === 0 && (
        <p style={{ color: '#65676b', fontSize: '0.9rem' }}>
          No friends yet. Add someone above!
        </p>
      )}
    </div>
  )
}
