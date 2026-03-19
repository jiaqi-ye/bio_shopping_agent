export default function TopNavbar({ onRunAgent, lastRunLabel }) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Research Animals Procurement Agent</p>
        <h1 className="text-2xl font-semibold text-slate-900">Procurement Command Center</h1>
        <p className="muted">Simulated AI agent workflow for biotech operations planning.</p>
      </div>
      <div className="flex items-center gap-3">
        <div className="card px-4 py-2">
          <p className="text-xs text-slate-400">Last Agent Run</p>
          <p className="text-sm font-semibold text-slate-900">{lastRunLabel}</p>
        </div>
        <button className="button-primary" onClick={onRunAgent}>
          Run Procurement Agent
        </button>
      </div>
    </header>
  );
}
