export default function MetricCard({ title, value, trend, trendLabel }) {
  const trendColor = trend > 0 ? "text-emerald-500" : trend < 0 ? "text-rose-500" : "text-slate-400";
  const trendSymbol = trend > 0 ? "▲" : trend < 0 ? "▼" : "●";

  return (
    <div className="card p-6 flex flex-col gap-3">
      <p className="text-sm text-slate-500">{title}</p>
      <div className="flex items-baseline justify-between">
        <p className="metric-value">{value}</p>
        <p className={`text-sm font-medium ${trendColor}`}>
          {trendSymbol} {Math.abs(trend)}% {trendLabel}
        </p>
      </div>
    </div>
  );
}
