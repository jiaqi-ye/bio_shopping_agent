export default function VendorCard({ vendor }) {
  return (
    <div className="card p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{vendor.name}</h3>
          <p className="muted">Lead time {vendor.lead_time} days</p>
        </div>
        <span className="text-sm font-semibold text-brand-500">{vendor.reliability_score}%</span>
      </div>
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div>
          <p className="text-slate-400">Price</p>
          <p className="font-semibold text-slate-900">${vendor.price}</p>
        </div>
        <div>
          <p className="text-slate-400">Inventory</p>
          <p className="font-semibold text-slate-900">{vendor.inventory}</p>
        </div>
        <div>
          <p className="text-slate-400">Strain</p>
          <p className="font-semibold text-slate-900">{vendor.strain}</p>
        </div>
      </div>
    </div>
  );
}
