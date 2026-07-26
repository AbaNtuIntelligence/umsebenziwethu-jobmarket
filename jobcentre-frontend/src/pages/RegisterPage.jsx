import { useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import SocialSignInButtons from "../components/SocialSignInButtons";
import { errorMessage } from "../services/api";
import { useAuth } from "../state/AuthContext";

export default function RegisterPage() {
  const { socialLogin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const formRef = useRef(null);
  const [role, setRole] = useState("job_seeker");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function social(provider, idToken, providerError) {
    if (providerError) return setError(providerError.message);
    if (!formRef.current?.reportValidity()) return;
    const form = Object.fromEntries(new FormData(formRef.current));
    setBusy(true);
    setError("");
    try {
      const result = await socialLogin(provider, idToken, {
        role,
        organisation_name: form.organisation_name || "",
        accept_terms: form.accept_terms === "true",
      });
      navigate(result.user.role === "employer" ? "/employer" : "/profile", { replace: true });
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  return <div className="auth-card">
    <h1>Create your opportunity account</h1>
    <p>Choose your role, then sign up securely with Google or Microsoft.</p>
    {location.state?.message && <div className="alert">{location.state.message}</div>}
    <div className="role-picker">
      <button type="button" className={role === "job_seeker" ? "selected" : ""} onClick={() => setRole("job_seeker")}>I’m looking for work</button>
      <button type="button" className={role === "employer" ? "selected" : ""} onClick={() => setRole("employer")}>I’m hiring</button>
    </div>
    {error && <div className="alert error">{error}</div>}
    <form ref={formRef} className="form-stack" onSubmit={(event) => event.preventDefault()}>
      {role === "employer" && <label>Organisation name<input name="organisation_name" required /></label>}
      <label className="consent">
        <input type="checkbox" name="accept_terms" value="true" required />
        <span>I accept the <Link to="/privacy" target="_blank">Terms of Use and Privacy Notice</Link>.</span>
      </label>
    </form>
    <SocialSignInButtons onCredential={social} disabled={busy} label="Sign up" />
    <p className="onboarding-note">After sign-up, complete your contact details, work profile or organisation information from your Profile page.</p>
    <p>Already registered? <Link to="/login">Sign in</Link></p>
  </div>;
}
