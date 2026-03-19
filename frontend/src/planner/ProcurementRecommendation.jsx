export default function ProcurementRecommendation({ plan }) {
  if (!plan) {
    return (
      <div className="card p-6">
        <h2 className="text-xl font-semibold text-slate-900">Procurement Recommendation</h2>
        <p className="muted">Run the agent to generate a recommendation.</p>
      </div>
    );
  }

  return (
    <div className="card p-6">
      <h2 className="text-xl font-semibold text-slate-900">Recommended Procurement Plan</h2>
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-slate-400">Best Vendor</p>
          <p className="text-lg font-semibold text-slate-900">{plan.bestVendor}</p>
        </div>
        <div>
          <p className="text-slate-400">Estimated Delivery</p>
          <p className="text-lg font-semibold text-slate-900">{plan.estimatedDelivery}</p>
        </div>
        <div>
          <p className="text-slate-400">Total Cost</p>
          <p className="text-lg font-semibold text-slate-900">${plan.totalCost}</p>
        </div>
        <div>
          <p className="text-slate-400">Compliance Status</p>
          <p className={`text-lg font-semibold ${plan.complianceStatus === "Approved" ? "text-emerald-500" : "text-amber-500"}`}>
            {plan.complianceStatus}
          </p>
        </div>
      </div>
      <div className="mt-4">
        <p className="text-slate-400 text-sm">Vendor Allocation</p>
        <div className="mt-2 space-y-2">
          {plan.allocation.map((item) => (
            <div key={item.vendor} className="flex items-center justify-between border border-gray-200 rounded-lg px-3 py-2 text-sm">
              <span className="font-semibold text-slate-900">{item.vendor}</span>
              <span className="text-slate-500">{item.quantity} mice</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
