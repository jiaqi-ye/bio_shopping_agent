import { useEffect, useState } from "react";
import logoUrl from "../assets/logo.svg";

type LoginModalProps = {
  open: boolean;
  onSubmit: (payload: {
    username: string;
    lab_institution: string;
    contact_info: string;
    password: string;
    shipping_address: string;
    current_mouse_count: number;
    cage_capacity: number;
  }) => Promise<void> | void;
  initialValues?: Partial<{
    username: string;
    lab_institution: string;
    contact_info: string;
    password: string;
    shipping_address: string;
    current_mouse_count: number;
    cage_capacity: number;
  }>;
  title?: string;
  description?: string;
  submitLabel?: string;
  onClose?: () => void;
};

export default function LoginModal({
  open,
  onSubmit,
  initialValues,
  title = "Lab User Login",
  description = "Provide your lab profile to continue.",
  submitLabel = "Sign in",
  onClose
}: LoginModalProps) {
  const [username, setUsername] = useState("");
  const [labInstitution, setLabInstitution] = useState("");
  const [contactInfo, setContactInfo] = useState("");
  const [password, setPassword] = useState("");
  const [shippingAddress, setShippingAddress] = useState("");
  const [currentMouseCount, setCurrentMouseCount] = useState("");
  const [cageCapacity, setCageCapacity] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setUsername(initialValues?.username ?? "");
    setLabInstitution(initialValues?.lab_institution ?? "");
    setContactInfo(initialValues?.contact_info ?? "");
    setPassword(initialValues?.password ?? "");
    setShippingAddress(initialValues?.shipping_address ?? "");
    setCurrentMouseCount(
      initialValues?.current_mouse_count !== undefined
        ? String(initialValues.current_mouse_count)
        : ""
    );
    setCageCapacity(
      initialValues?.cage_capacity !== undefined ? String(initialValues.cage_capacity) : ""
    );
  }, [open, initialValues]);

  if (!open) return null;

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      await onSubmit({
        username: username.trim(),
        lab_institution: labInstitution.trim(),
        contact_info: contactInfo.trim(),
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
      <div className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        {onClose ? (
          <button
            type="button"
            onClick={onClose}
            className="absolute right-3 top-3 text-slate-400 hover:text-slate-600"
            aria-label="Close"
          >
            ✕
          </button>
        ) : null}
        <div className="flex flex-col items-center">
          <img src={logoUrl} alt="BioShopping Agent" className="h-24 w-24" />
          <h2 className="mt-3 text-lg font-semibold text-slate-900">{title}</h2>
        </div>
        <p className="mt-1 text-xs text-slate-500">{description}</p>
        <div className="mt-4 grid gap-3">
          <input
            className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
            placeholder="Lab / Institution"
            value={labInstitution}
            onChange={(e) => setLabInstitution(e.target.value)}
          />
          <input
            className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
            placeholder="Contact information (email/phone)"
            value={contactInfo}
            onChange={(e) => setContactInfo(e.target.value)}
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
          disabled={
            loading ||
            !username.trim() ||
            !labInstitution.trim() ||
            !contactInfo.trim() ||
            !password.trim() ||
            !shippingAddress.trim()
          }
          className="mt-4 w-full rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
        >
          {loading ? "Saving..." : submitLabel}
        </button>
      </div>
    </div>
  );
}
