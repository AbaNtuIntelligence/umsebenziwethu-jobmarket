import { CheckCircle2, MessageSquareText, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { errorMessage } from "../services/api";
import { useAuth } from "../state/AuthContext";

export default function VerifyPhonePage() {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (user?.phone_verified_at) navigate(user.role === "employer" ? "/employer" : "/", { replace: true });
  }, [user, navigate]);

  async function sendCode() {
    setBusy(true); setError(""); setMessage("");
    try {
      const { data } = await api.post("/auth/phone-otp/send/");
      setSent(true); setMessage(data.detail);
    } catch (requestError) { setError(errorMessage(requestError)); }
    finally { setBusy(false); }
  }

  async function verify(event) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const code = new FormData(event.currentTarget).get("code");
      const { data } = await api.post("/auth/phone-otp/verify/", { code });
      updateUser(data.user); setMessage(data.detail);
    } catch (requestError) { setError(errorMessage(requestError)); }
    finally { setBusy(false); }
  }

  return <div className="auth-card phone-verification-card">
    <ShieldCheck className="phone-verification-shield" />
    <h1>Verify your mobile number</h1>
    <p>We use a one-time SMS code to confirm that you control <b>{user?.phone}</b>. This does not guarantee a person or organisation’s future conduct.</p>
    {message && <div className="alert"><CheckCircle2 /> {message}</div>}
    {error && <div className="alert error">{error}</div>}
    {!sent ? <button className="button primary full" disabled={busy} onClick={sendCode}><MessageSquareText />{busy ? "Sending code…" : "Send verification code"}</button> : <form className="form-stack" onSubmit={verify}>
      <label>Six-digit code<input name="code" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength="6" required autoFocus /></label>
      <button className="button primary" disabled={busy}>{busy ? "Checking code…" : "Verify phone"}</button>
      <button type="button" className="button ghost" disabled={busy} onClick={sendCode}>Send another code</button>
    </form>}
    <small>Codes expire after 10 minutes. Never share this code with another person.</small>
  </div>;
}
