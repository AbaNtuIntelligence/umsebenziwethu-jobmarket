import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import SocialSignInButtons from "../components/SocialSignInButtons";
import { errorMessage } from "../services/api";
import { useAuth } from "../state/AuthContext";

export default function LoginPage() {
  const { login, socialLogin, sessionExpired } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState("");
  const [pendingLink, setPendingLink] = useState(null);
  const [busy, setBusy] = useState(false);

  function destination(user) {
    return location.state?.from?.pathname || (user.role === "employer" ? "/employer" : "/");
  }

  async function social(provider, idToken, providerError) {
    if (providerError) return setError(providerError.message);
    setBusy(true);
    setError("");
    try {
      const result = await socialLogin(provider, idToken);
      navigate(destination(result.user), { replace: true });
    } catch (requestError) {
      if (requestError.response?.data?.code === "link_required") {
        setPendingLink({ provider, idToken, email: requestError.response.data.email });
      } else if (requestError.response?.data?.code === "registration_required") {
        navigate("/register", { state: { message: "Choose your account type before signing up." } });
      } else {
        setError(errorMessage(requestError));
      }
    } finally {
      setBusy(false);
    }
  }

  async function linkExisting(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const password = new FormData(event.currentTarget).get("password");
      const result = await socialLogin(pendingLink.provider, pendingLink.idToken, { link_password: password });
      navigate(destination(result.user), { replace: true });
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function passwordLogin(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const user = await login(data.email, data.password);
      navigate(destination(user), { replace: true });
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  return <div className="auth-card">
    <h1>Welcome back</h1>
    <p>Use a trusted account to continue to UmsebenziWethu.</p>
    {sessionExpired && !error && <div className="alert">Your session expired safely. Please sign in again.</div>}
    {location.state?.registered && <div className="alert">Account created. You may now sign in.</div>}
    {error && <div className="alert error">{error}</div>}
    {pendingLink ? (
      <form className="form-stack link-account-box" onSubmit={linkExisting}>
        <h2>Link your existing account</h2>
        <p>{pendingLink.email} already belongs to an UmsebenziWethu account. Enter its current password once to link it safely.</p>
        <label>Existing account password<input type="password" name="password" required autoFocus /></label>
        <button className="button primary" disabled={busy}>{busy ? "Linking…" : "Link and continue"}</button>
        <button type="button" className="button ghost" onClick={() => setPendingLink(null)}>Cancel</button>
      </form>
    ) : (
      <>
        <SocialSignInButtons onCredential={social} disabled={busy} />
        <div className="auth-divider"><span>Existing pilot account</span></div>
        <details className="legacy-login">
          <summary>Sign in with email and password</summary>
          <form onSubmit={passwordLogin} className="form-stack">
            <label>Email<input type="email" name="email" required /></label>
            <label>Password<input type="password" name="password" required /></label>
            <Link to="/forgot-password">Forgot your password?</Link>
            <button className="button primary" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
          </form>
        </details>
      </>
    )}
    <p>New here? <Link to="/register">Create an account</Link></p>
    <small className="social-safety-note">Social sign-in confirms control of the selected online account. Employer verification remains a separate safety check.</small>
  </div>;
}
