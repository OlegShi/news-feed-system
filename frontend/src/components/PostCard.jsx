export default function PostCard({ post }) {
  const initial = (post.username || '?')[0].toUpperCase()
  const time = new Date(post.created_at).toLocaleString()

  return (
    <div className="post-card">
      <div className="post-header">
        <div className="avatar">{initial}</div>
        <div className="post-meta">
          <div className="username">{post.username}</div>
          <div className="timestamp">{time}</div>
        </div>
      </div>
      <div className="post-content">{post.content}</div>
    </div>
  )
}
