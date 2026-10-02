import { useEffect, useState, useCallback } from "react";
import { fetchComplaints, fetchStats, updateStatus, resolveComplaint, fileUrl } from "./api/client.js";
import TrendChart from "./TrendChart.jsx";

const STATUS_OPTIONS = ["submitted", "in_progress", "resolved"];

export default function App() {
  const [complaints, setComplaints] = useState([]);
  const [stats, setStats] = useState(null);
  const [loadState, setLoadState] = useState("loading"); // loading | loaded | error
  const [error, setError] = useState(null);

  const [statusFilter, setStatusFilter] = useState("");
  const [issueTypeFilter, setIssueTypeFilter] = useState("");

  const [resolving, setResolving] = useState(null); // complaint being resolved
  const [saving, setSaving] = useState(false);

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
    // "Resolved" opens the dialog so the admin can attach an after photo
    if (newStatus === "resolved") {
      setResolving(complaints.find((c) => c.id === id) || null);
      return;
    }
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

  async function confirmResolve(file) {
    setSaving(true);
    try {
      await resolveComplaint(resolving.id, file);
      setResolving(null);
      load();
    } catch (err) {
      alert(`Could not resolve complaint: ${err.message}`);
    } finally {
      setSaving(false);
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

      <div className="section-title">Complaints by category</div>
      <div className="card" style={{ padding: 16, marginBottom: 24 }}>
        <TrendChart byCategory={stats?.by_category} />
      </div>

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

      {resolving && (
        <ResolveDialog
          complaint={resolving}
          saving={saving}
          onCancel={() => setResolving(null)}
          onConfirm={confirmResolve}
        />
      )}
    </div>
  );
}

function StatsRow({ stats, totalKnown }) {
  // If the stats endpoint isn't available, fall back to counting what we
  // already loaded rather than inventing numbers.
  const total = stats?.total ?? totalKnown;
  const submitted = stats?.by_status?.submitted ?? "—";
  const inProgress = stats?.by_status?.in_progress ?? "—";
  const resolved = stats?.by_status?.resolved ?? "—";

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

function PhotoCell({ c }) {
  const before = fileUrl(c.photo_url);
  const after = fileUrl(c.after_photo_url);

  if (!before && !after) return <span className="muted">No photo</span>;

  return (
    <div style={styles.photoPair}>
      {before && (
        <a href={before} target="_blank" rel="noreferrer" style={styles.thumbWrap}>
          <img src={before} alt="Before" style={styles.thumb} />
          <span style={styles.thumbLabel}>Before</span>
        </a>
      )}
      {after && (
        <a href={after} target="_blank" rel="noreferrer" style={styles.thumbWrap}>
          <img src={after} alt="After" style={styles.thumb} />
          <span style={styles.thumbLabel}>After</span>
        </a>
      )}
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
            <th>Photos</th>
            <th>Status</th>
            <th>Reported</th>
          </tr>
        </thead>
        <tbody>
          {complaints.map((c) => (
            <tr key={c.id}>
              <td>{String(c.id).slice(0, 8)}</td>
              <td>{c.issue_type ?? <span className="muted">AI: unavailable</span>}</td>
              <td>
                {c.priority_score != null
                  ? c.priority_score
                  : <span className="muted">Not available</span>}
              </td>
              <td>
                {c.lat != null && c.lng != null
                  ? `${c.lat.toFixed(4)}, ${c.lng.toFixed(4)}`
                  : <span className="muted">—</span>}
              </td>
              <td><PhotoCell c={c} /></td>
              <td>
                <span className={`badge badge--${c.status}`} style={{ marginRight: 8 }}>
                  {formatStatus(c.status)}
                </span>
                {c.escalated && <span className="badge-escalated">Escalated</span>}
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

function ResolveDialog({ complaint, saving, onCancel, onConfirm }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const before = fileUrl(complaint.photo_url);

  return (
    <div style={styles.overlay}>
      <div className="card" style={styles.dialog}>
        <h2 style={{ marginTop: 0 }}>Mark as resolved</h2>
        <p className="muted">
          Optional: attach an "after" photo so the fix can be checked against the original report.
        </p>

        <div style={styles.compare}>
          <div>
            <div style={styles.compareLabel}>Before</div>
            {before
              ? <img src={before} alt="Before" style={styles.compareImg} />
              : <div style={styles.noImg}>No photo reported</div>}
          </div>
          <div>
            <div style={styles.compareLabel}>After</div>
            {preview
              ? <img src={preview} alt="After preview" style={styles.compareImg} />
              : <div style={styles.noImg}>No after photo yet</div>}
          </div>
        </div>

        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          style={{ marginBottom: 16 }}
        />

        <div style={styles.dialogActions}>
          <button onClick={onCancel} disabled={saving} style={styles.refreshBtn}>Cancel</button>
          <button onClick={() => onConfirm(file)} disabled={saving} style={styles.primaryBtn}>
            {saving ? "Saving…" : "Confirm resolved"}
          </button>
        </div>
      </div>
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
  primaryBtn: {
    background: "var(--color-text, #1a1a1a)",
    color: "#fff",
    border: "none",
    borderRadius: "var(--radius-sm)",
    padding: "8px 16px",
    fontWeight: 500
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 14,
    marginBottom: 24
  },
  photoPair: { display: "flex", gap: 8 },
  thumbWrap: { display: "block", textAlign: "center", textDecoration: "none", color: "inherit" },
  thumb: { width: 56, height: 56, objectFit: "cover", borderRadius: 4, border: "1px solid var(--color-border)", display: "block" },
  thumbLabel: { fontSize: 11, color: "var(--color-muted, #666)" },
  overlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.4)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
    zIndex: 10
  },
  dialog: { width: "100%", maxWidth: 560, padding: 24, background: "var(--color-surface, #fff)" },
  compare: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, margin: "16px 0" },
  compareLabel: { fontSize: 13, fontWeight: 600, marginBottom: 6 },
  compareImg: { width: "100%", height: 180, objectFit: "cover", borderRadius: 4, border: "1px solid var(--color-border)" },
  noImg: {
    height: 180,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    border: "1px dashed var(--color-border)",
    borderRadius: 4,
    fontSize: 13,
    color: "var(--color-muted, #666)"
  },
  dialogActions: { display: "flex", justifyContent: "flex-end", gap: 8 }
};
