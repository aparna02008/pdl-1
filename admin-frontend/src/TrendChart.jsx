import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function TrendChart({ byCategory }) {
  const data = Object.entries(byCategory || {}).map(([name, count]) => ({ name, count }));

  if (data.length === 0) {
    return <p>No categorised complaints yet.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data}>
        <XAxis dataKey="name" />
        <YAxis allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="count" fill="#3b5b8c" />
      </BarChart>
    </ResponsiveContainer>
  );
}