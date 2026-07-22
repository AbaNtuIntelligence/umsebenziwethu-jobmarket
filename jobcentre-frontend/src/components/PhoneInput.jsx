import { useState } from "react";

function nationalNumber(value = "") {
  const digits = String(value).replace(/\D/g, "");
  if (digits.startsWith("27") && digits.length === 11) return digits.slice(2);
  if (digits.startsWith("0") && digits.length === 10) return digits.slice(1);
  return digits.slice(0, 9);
}

export default function PhoneInput({ defaultValue = "", required = true, label = "Mobile number" }) {
  const [number, setNumber] = useState(() => nationalNumber(defaultValue));

  function change(event) {
    setNumber(event.target.value.replace(/\D/g, "").slice(0, 9));
  }

  return <label className="phone-field">
    {label}
    <span className="phone-input-shell">
      <b aria-hidden="true">+27</b>
      <input
        value={number}
        onChange={change}
        type="tel"
        inputMode="numeric"
        autoComplete="tel-national"
        placeholder="73 086 2149"
        pattern="[6-8][0-9]{8}"
        title="Enter the nine digits after +27, for example 73 086 2149."
        required={required}
        aria-label={`${label}, digits after plus 27`}
      />
    </span>
    <input type="hidden" name="phone" value={number ? `+27${number}` : ""} />
    <small>Enter the 9 digits after +27. Example: 73 086 2149.</small>
  </label>;
}
