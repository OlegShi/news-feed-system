import { useState } from 'react'
import { publishPost } from '../services/api'

export default function PostForm({ token, onPostCreated }) {
  const [content, setContent] = useState('')
  const [posting, setPosting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!content.trim()) return

    setPosting(true)
    try {
      await publishPost(token, content)
      setContent('')
      onPostCreated()
    } catch (err) {
      alert(err.message)
    } finally {
      setPosting(false)
    }
  }

  return (
    <form className="post-form" onSubmit={handleSubmit}>
      <textarea
        placeholder="What's on your mind?"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={3}
      />
      <button type="submit" disabled={posting || !content.trim()}>
        {posting ? 'Posting...' : 'Post'}
      </button>
      <div style={{ clear: 'both' }} />
    </form>
  )
}
