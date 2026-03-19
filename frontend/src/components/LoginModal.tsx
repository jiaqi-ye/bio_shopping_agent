import { useState } from "react";

type LoginModalProps = {
  open: boolean;
  onSubmit: (payload: {
    username: string;
    password: string;
    shipping_address: string;
    current_mouse_count: number;
    cage_capacity: number;
  }) => Promise<void> | void;
};

export default function LoginModal({ open, onSubmit }: LoginModalProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [shippingAddress, setShippingAddress] = useState("");
  const [currentMouseCount, setCurrentMouseCount] = useState("0");
  const [cageCapacity, setCageCapacity] = useState("0");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!open) return null;

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      await onSubmit({
        username: username.trim(),
        password,
        shipping_address: shippingAddress.trim(),
        current_mouse_count: Number(currentMouseCount || 0),
        cage_capacity: Number(cageCapacity || 0)
      });
    } catch (err) {
      setError("Login failed. Please check the fields.");
      setLoading(false);
      return;
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-slate-900">Lab User Login</h2>
        <p className="mt-1 text-xs text-slate-500">Provide your lab profile to continue.</p>
        <div className="mt-4 grid gap-3">
          <input
            className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <input
            className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
            placeholder="Shipping address"
            value={shippingAddress}
            onChange={(e) => setShippingAddress(e.target.value)}
          />
          <div className="grid grid-cols-2 gap-3">
            <input
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
              placeholder="Current mouse count"
              inputMode="numeric"
              value={currentMouseCount}
              onChange={(e) => setCurrentMouseCount(e.target.value)}
            />
            <input
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
              placeholder="Cage capacity"
              inputMode="numeric"
              value={cageCapacity}
              onChange={(e) => setCageCapacity(e.target.value)}
            />
          </div>
        </div>
        {error ? <p className="mt-3 text-xs text-rose-600">{error}</p> : null}
        <button
          type="button"
          onClick={handleSubmit}
          disabled={loading || !username.trim() || !password.trim() || !shippingAddress.trim()}
          className="mt-4 w-full rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </div>
    </div>
  );
}
