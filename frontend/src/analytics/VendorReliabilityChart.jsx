import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function VendorReliabilityChart({ data }) {
  return (
    <div className="card p-6 h-full">
      <h3 className="text-lg font-semibold text-slate-900">Vendor Reliability Score</h3>
      <div className="mt-4 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="name" tickLine={false} axisLine={false} />
            <YAxis tickLine={false} axisLine={false} domain={[80, 100]} />
            <Tooltip cursor={{ fill: "#EFF6FF" }} />
            <Bar dataKey="score" fill="#2563EB" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
