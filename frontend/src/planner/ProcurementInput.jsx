export default function ProcurementInput({ values, onChange, onRun }) {
  return (
    <div className="card p-6">
      <h2 className="text-xl font-semibold text-slate-900">Interactive Procurement Input</h2>
      <p className="muted">Enter experiment parameters to run the procurement agent.</p>
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <label className="flex flex-col gap-2">
          <span className="text-slate-500">Mouse Strain</span>
          <input
            className="border border-gray-200 rounded-lg px-3 py-2"
            value={values.strain}
            onChange={(event) => onChange("strain", event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-slate-500">Quantity</span>
          <input
            type="number"
            min="1"
            className="border border-gray-200 rounded-lg px-3 py-2"
            value={values.quantity}
            onChange={(event) => onChange("quantity", Number(event.target.value))}
          />
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-slate-500">Experiment Start Date</span>
          <input
            type="date"
            className="border border-gray-200 rounded-lg px-3 py-2"
            value={values.experimentStart}
            onChange={(event) => onChange("experimentStart", event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-slate-500">Mice Per Cage</span>
          <input
            type="number"
            min="1"
            className="border border-gray-200 rounded-lg px-3 py-2"
            value={values.micePerCage}
            onChange={(event) => onChange("micePerCage", Number(event.target.value))}
          />
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-slate-500">Available Cages</span>
          <input
            type="number"
            min="1"
            className="border border-gray-200 rounded-lg px-3 py-2"
            value={values.availableCages}
            onChange={(event) => onChange("availableCages", Number(event.target.value))}
          />
        </label>
      </div>
      <button className="button-primary mt-5" onClick={onRun}>Run Procurement Agent</button>
    </div>
  );
}
