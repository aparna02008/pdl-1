// A complaint is escalated if it is still "submitted" after this many days
export const ESCALATION_DAYS = 7;

export function isEscalated(c) {
  if (c.status !== "submitted") return false; // match the exact status text from your backend
  const created = new Date(c.created_at.endsWith("Z") ? c.created_at : c.created_at + "Z");
  const days = (Date.now() - created.getTime()) / (1000 * 60 * 60 * 24);
  return days > ESCALATION_DAYS;
}