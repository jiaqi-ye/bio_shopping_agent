import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function PriceTrendChart({ data }) {
  return (
    <div className="card p-6 h-full">
      <h3 className="text-lg font-semibold text-slate-900">Price Trend</h3>
      <div className="mt-4 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <XAxis dataKey="month" tickLine={false} axisLine={false} />
            <YAxis tickLine={false} axisLine={false} />
            <Tooltip cursor={{ stroke: "#E5E7EB" }} />
            <Area type="monotone" dataKey="price" stroke="#2563EB" fill="#DBEAFE" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
