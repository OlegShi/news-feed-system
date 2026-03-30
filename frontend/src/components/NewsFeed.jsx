import { useState, useEffect } from 'react'
import { getFeed } from '../services/api'
import PostCard from './PostCard'

export default function NewsFeed({ token, refreshTrigger }) {
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)

  const loadFeed = async () => {
    try {
      const data = await getFeed(token)
      setPosts(data.feed)
    } catch (err) {
      console.error('Failed to load feed:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFeed()
    const interval = setInterval(loadFeed, 10000) // poll every 10s
    return () => clearInterval(interval)
  }, [token, refreshTrigger])

  if (loading) {
    return <div className="loading">Loading feed...</div>
  }

  if (posts.length === 0) {
    return (
      <div className="empty-feed">
        <h3>No posts yet</h3>
        <p>Add friends and start posting to see content here.</p>
      </div>
    )
  }

  return (
    <div>
      {posts.map((post) => (
        <PostCard key={post.post_id} post={post} />
      ))}
    </div>
  )
}
