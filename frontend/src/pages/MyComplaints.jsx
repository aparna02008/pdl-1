import { useEffect, useState } from 'react'
import { fetchComplaints } from '../api/complaints'
import { IconEmptyBox, IconAlert } from '../components/Icons'

const STATUS_LABEL = {
  submitted: 'Submitted',
  in_progress: 'In progress',
  resolved: 'Resolved',
}

export default function MyComplaints() {
  const [state, setState] = useState({ loading: true, error: null, data: [] })

  useEffect(() => {
    let cancelled = false
    fetchComplaints()
      .then((data) => { if (!cancelled) setState({ loading: false, error: null, data }) })
      .catch((err) => { if (!cancelled) setState({ loading: false, error: err.message, data: [] }) })
    return () => { cancelled = true }
  }, [])

  return (
    <div className="page-content">
      <div className="page-header">
        <h1>My complaints</h1>
        <p>Track the status of issues you've reported.</p>
      </div>

      <div className="card">
        {state.loading && (
          <>
            <div className="skeleton-row" />
            <div className="skeleton-row" />
            <div className="skeleton-row" />
          </>
        )}

        {!state.loading && state.error && (
          <div className="banner banner--error">
            <IconAlert width={16} height={16} />
            <span>Couldn't load your complaints — {state.error}</span>
          </div>
        )}

        {!state.loading && !state.error && state.data.length === 0 && (
          <div className="empty-state">
            <IconEmptyBox />
            <p>You haven't reported anything yet. Reports you submit will show up here.</p>
          </div>
        )}

        {!state.loading && !state.error && state.data.map((c) => (
          <div className="complaint" key={c.id}>
            {c.photo_url && <img className="complaint__thumb" src={c.photo_url} alt="" />}
            <div className="complaint__body">
              <div className="complaint__top">
                <span className="complaint__desc">{c.description}</span>
                <span className={`status-pill status-pill--${c.status}`}>
                  {STATUS_LABEL[c.status] || c.status}
                </span>
              </div>
              <div className="complaint__meta">
                {c.address || (c.lat ? `${c.lat.toFixed(4)}, ${c.lng.toFixed(4)}` : 'No location')} · {new Date(c.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
