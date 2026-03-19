import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function LeadTimeChart({ data }) {
  return (
    <div className="card p-6 h-full">
      <h3 className="text-lg font-semibold text-slate-900">Lead Time Prediction</h3>
      <div className="mt-4 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="week" tickLine={false} axisLine={false} />
            <YAxis tickLine={false} axisLine={false} />
            <Tooltip cursor={{ stroke: "#E5E7EB" }} />
            <Line type="monotone" dataKey="days" stroke="#2563EB" strokeWidth={3} dot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
