export default function RFQForm({ experimentStartDate, vendorLeadTime, latestOrderDate }) {
  return (
    <div className="card p-5">
      <h3 className="text-lg font-semibold text-slate-900">Lead Time Planning</h3>
      <p className="muted">Latest order date computed from experiment start and lead time.</p>
      <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
        <div>
          <p className="text-slate-400">Experiment Start</p>
          <p className="font-semibold text-slate-900">{experimentStartDate}</p>
        </div>
        <div>
          <p className="text-slate-400">Vendor Lead Time</p>
          <p className="font-semibold text-slate-900">{vendorLeadTime} days</p>
        </div>
        <div>
          <p className="text-slate-400">Latest Order Date</p>
          <p className="font-semibold text-slate-900">{latestOrderDate}</p>
        </div>
      </div>
    </div>
  );
}
