export default function ReasoningStepCard({ step, title, summary, details, isOpen, onToggle }) {
  return (
    <div className="card p-5">
      <button
        onClick={onToggle}
        className="w-full flex items-start justify-between gap-3 text-left"
      >
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Step {step}</p>
          <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
          <p className="muted mt-1">{summary}</p>
        </div>
        <span className={`text-sm font-semibold ${isOpen ? "text-brand-500" : "text-slate-400"}`}>
          {isOpen ? "Hide" : "Expand"}
        </span>
      </button>
      {isOpen && <div className="mt-4 space-y-3 text-sm text-slate-600">{details}</div>}
    </div>
  );
}
