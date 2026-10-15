import { useMemo, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { severityLabel, priorityLabel } from "./labels.js";

// Leaflet's default marker icons reference image files that don't bundle
// correctly with Vite. Rebuilding the icon URLs from the installed package
// avoids broken/missing pin images.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL("leaflet/dist/images/marker-icon-2x.png", import.meta.url).href,
  iconUrl: new URL("leaflet/dist/images/marker-icon.png", import.meta.url).href,
  shadowUrl: new URL("leaflet/dist/images/marker-shadow.png", import.meta.url).href,
});

// Rounds coordinates to ~100m precision so nearby reports of the same real
// spot group into one pin instead of one pin per exact GPS reading.
function areaKey(lat, lng) {
  return `${lat.toFixed(3)},${lng.toFixed(3)}`;
}

function groupByArea(complaints) {
  const groups = new Map();
  for (const c of complaints) {
    if (c.lat == null || c.lng == null) continue;
    const key = areaKey(c.lat, c.lng);
    if (!groups.has(key)) {
      groups.set(key, { lat: c.lat, lng: c.lng, complaints: [] });
    }
    groups.get(key).complaints.push(c);
  }
  return Array.from(groups.values());
}

export default function MapView({ complaints, onSelectComplaint }) {
  const areas = useMemo(() => groupByArea(complaints), [complaints]);
  const [activeAreaKey, setActiveAreaKey] = useState(null);

  if (areas.length === 0) {
    return <p className="muted">No complaints with a location yet.</p>;
  }

  // Center the map on the first area with reports; a real deployment
  // might center on the city/ward instead, but this keeps it accurate to
  // real data rather than hardcoding a guessed location.
  const center = [areas[0].lat, areas[0].lng];

  return (
    <div style={{ borderRadius: "var(--radius-md)", overflow: "hidden" }}>
      <MapContainer center={center} zoom={15} style={{ height: 360, width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {areas.map((area) => {
          const key = areaKey(area.lat, area.lng);
          const pending = area.complaints.filter((c) => c.status !== "resolved").length;
          return (
            <Marker
              key={key}
              position={[area.lat, area.lng]}
              eventHandlers={{ click: () => setActiveAreaKey(key) }}
            >
              <Popup>
                <div style={{ minWidth: 200 }}>
                  <strong>{area.complaints.length} report{area.complaints.length > 1 ? "s" : ""} here</strong>
                  {pending > 0 && <div style={{ color: "#a23b1e", fontSize: 13 }}>{pending} still pending</div>}
                  <div style={{ marginTop: 8, maxHeight: 220, overflowY: "auto" }}>
                    {area.complaints.map((c) => (
                      <div
                        key={c.id}
                        onClick={() => onSelectComplaint && onSelectComplaint(c)}
                        style={{
                          padding: "6px 0",
                          borderBottom: "1px solid #eee",
                          cursor: onSelectComplaint ? "pointer" : "default",
                        }}
                      >
                        <div style={{ fontWeight: 600, fontSize: 13 }}>
                          {c.issue_type || "Unidentified issue"} — {c.status}
                        </div>
                        <div style={{ fontSize: 12, color: "#666" }}>
                          Severity: {severityLabel(c.severity_score) || "Not available"} ·
                          {" "}Priority: {priorityLabel(c.priority_score) || "Not available"}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
