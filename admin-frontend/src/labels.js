// Maps the raw 1/2/3 numbers from the trained model to the real meaning,
// taken directly from backend/labeling_rules.txt. Keep this file in sync
// if the labeling rules ever change.

export const SEVERITY_LABELS = {
  1: "Minor",
  2: "Affects daily life",
  3: "Safety risk",
};

export const PRIORITY_LABELS = {
  1: "Low",
  2: "Medium",
  3: "High",
};

export function severityLabel(value) {
  if (value == null) return null;
  return SEVERITY_LABELS[Math.round(value)] || `Level ${Math.round(value)}`;
}

export function priorityLabel(value) {
  if (value == null) return null;
  return PRIORITY_LABELS[Math.round(value)] || `Level ${Math.round(value)}`;
}
