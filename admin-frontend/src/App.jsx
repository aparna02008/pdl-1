import { useEffect, useState, useCallback } from "react";
import { fetchComplaints, fetchStats, updateStatus } from "./api/client.js";

const STATUS_OPTIONS = ["submitted", "in_progress", "resolved"];

export default function App() {
  const [complaints, setComplaints] = useState([]);
  const [stats, setStats] = useState(null);
  const [loadState, setLoadState] = useState("loading"); // loading | loaded | error
  const [error, setError] = useState(null);

  const [statusFilter, setStatusFilter] = useState("");
  const [issueTypeFilter, setIssueTypeFilter] = useState("");

  const load = useCallback(() => {
    setLoadState("loading");
    setError(null);
    Promise.all([
      fetchComplaints({ status: statusFilter || undefined, issueType: issueTypeFilter || undefined }),
      fetchStats().catch(() => null) // stats endpoint failing shouldn't block the whole page
    ])
      .then(([complaintsData, statsData]) => {
        setComplaints(complaintsData);
        setStats(statsData);
        setLoadState("loaded");
      })
      .catch((err) => {
        setError(err.message || "Could not reach the server.");
        setLoadState("error");
      });
  }, [statusFilter, issueTypeFilter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleStatusChange(id, newStatus) {
    // optimistic update, rolled back on failure
    const previous = complaints;
    setComplaints((prev) => prev.map((c) => (c.id === id ? { ...c, status: newStatus } : c)));
    try {
      await updateStatus(id, newStatus);
      load(); // refresh stats too
    } catch (err) {
      setComplaints(previous);
      alert(`Could not update status: ${err.message}`);
    }
  }

  const issueTypes = Array.from(new Set(complaints.map((c) => c.issue_type).filter(Boolean)));

  const pending = complaints.filter((c) => c.status !== "resolved");
  const resolved = complaints.filter((c) => c.status === "resolved");

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div>
          <h1>CiviSense Admin</h1>
          <p>Complaints, priorities, and resolution status.</p>
        </div>
        <button onClick={load} style={styles.refreshBtn}>Refresh</button>
      </header>

      <StatsRow stats={stats} totalKnown={complaints.length} />

      <div className="filter-bar">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{formatStatus(s)}</option>
          ))}
        </select>

        <select value={issueTypeFilter} onChange={(e) => setIssueTypeFilter(e.target.value)}>
          <option value="">All issue types</option>
          {issueTypes.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {loadState === "loading" && <p className="muted">Loading complaints…</p>}

      {loadState === "error" && (
        <div className="card" style={{ padding: 16, color: "var(--color-danger)", background: "var(--color-danger-soft)" }}>
          Couldn't reach the server: {error}
        </div>
      )}

      {loadState === "loaded" && (
        <>
          <div className="section-title">
            Needs attention <span className="count-pill">{pending.length}</span>
          </div>
          <ComplaintTable complaints={pending} onStatusChange={handleStatusChange} emptyText="Nothing pending — all clear." />

          <div className="section-title">
            Resolved <span className="count-pill">{resolved.length}</span>
          </div>
          <ComplaintTable complaints={resolved} onStatusChange={handleStatusChange} emptyText="No resolved complaints yet." />
        </>
      )}
    </div>
  );
}

function StatsRow({ stats, totalKnown }) {
  // If the stats endpoint isn't available, fall back to counting what we
  // already loaded rather than inventing numbers.
  const total = stats?.total ?? totalKnown;
  const submitted = stats?.submitted ?? "—";
  const inProgress = stats?.in_progress ?? "—";
  const resolved = stats?.resolved ?? "—";

  return (
    <div style={styles.statsGrid}>
      <Stat label="Total" value={total} />
      <Stat label="Submitted" value={submitted} />
      <Stat label="In progress" value={inProgress} />
      <Stat label="Resolved" value={resolved} />
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function ComplaintTable({ complaints, onStatusChange, emptyText }) {
  if (complaints.length === 0) {
    return <div className="card"><div className="empty-row">{emptyText}</div></div>;
  }

  return (
    <div className="card" style={{ overflowX: "auto", marginBottom: 8 }}>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Issue type (AI)</th>
            <th>Priority</th>
            <th>Location</th>
            <th>Status</th>
            <th>Reported</th>
          </tr>
        </thead>
        <tbody>
          {complaints.map((c) => (
            <tr key={c.id}>
              <td>{c.id}</td>
              <td>{c.issue_type ?? <span className="muted">AI: unavailable</span>}</td>
              <td>
                {c.priority?.status === "unavailable" || c.priority == null
                  ? <span className="muted">Not available</span>
                  : c.priority}
              </td>
              <td>
                {c.latitude != null && c.longitude != null
                  ? `${c.latitude.toFixed(4)}, ${c.longitude.toFixed(4)}`
                  : <span className="muted">—</span>}
              </td>
              <td>
                <span className={`badge badge--${c.status}`} style={{ marginRight: 8 }}>
                  {formatStatus(c.status)}
                </span>
                <select
                  className="status-select"
                  value={c.status}
                  onChange={(e) => onStatusChange(c.id, e.target.value)}
                >
                  {STATUS_OPTIONS.map((s) => (
                    <option key={s} value={s}>{formatStatus(s)}</option>
                  ))}
                </select>
              </td>
              <td>{c.created_at ? new Date(c.created_at).toLocaleDateString() : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatStatus(status) {
  return { submitted: "Submitted", in_progress: "In progress", resolved: "Resolved" }[status] || status;
}

const styles = {
  page: {
    maxWidth: 1080,
    margin: "0 auto",
    padding: "40px 32px"
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 24
  },
  refreshBtn: {
    background: "var(--color-surface)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
    padding: "8px 16px",
    fontWeight: 500
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 14,
    marginBottom: 24
  }
};
