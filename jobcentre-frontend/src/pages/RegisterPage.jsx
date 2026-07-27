import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import SocialSignInButtons from "../components/SocialSignInButtons";
import PhoneInput from "../components/PhoneInput";
import { errorMessage } from "../services/api";
import { useAuth } from "../state/AuthContext";

export default function RegisterPage() {
  const { register, socialLogin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [role, setRole] = useState("job_seeker");
  const [organisationName, setOrganisationName] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function emailSignup(event) {
    event.preventDefault();
    setError("");

    const form = Object.fromEntries(new FormData(event.currentTarget));

    if (form.password !== form.confirm_password) {
      setError("The passwords do not match.");
      return;
    }

    if (!acceptedTerms) {
      setError("You must accept the Terms of Use and Privacy Notice.");
      return;
    }

    setBusy(true);

    try {
      const email = form.email.trim().toLowerCase();

      await register({
        username: email,
        email,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        phone: form.phone,
        password: form.password,
        role,
        organisation_name:
          role === "employer" ? organisationName.trim() : "",
        accept_terms: true,
      });

      navigate("/login", {
        replace: true,
        state: {
          registered: true,
        },
      });
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function social(provider, idToken, providerError) {
    if (providerError) {
      setError(providerError.message);
      return;
    }

    if (!acceptedTerms) {
      setError(
        "Accept the Terms of Use and Privacy Notice before continuing."
      );
      return;
    }

    if (role === "employer" && !organisationName.trim()) {
      setError("Enter your organisation name before continuing.");
      return;
    }

    setBusy(true);
    setError("");

    try {
      const result = await socialLogin(provider, idToken, {
        role,
        organisation_name:
          role === "employer" ? organisationName.trim() : "",
        accept_terms: true,
      });

      navigate(
        result.user.role === "employer" ? "/employer" : "/profile",
        { replace: true }
      );
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-card">
      <h1>Create your UmsebenziWethu account</h1>

      <p>
        Choose whether you are looking for work or recruiting, then create
        your account with email or Google.
      </p>

      {location.state?.message && (
        <div className="alert">{location.state.message}</div>
      )}

      <div className="role-picker">
        <button
          type="button"
          className={role === "job_seeker" ? "selected" : ""}
          onClick={() => setRole("job_seeker")}
          disabled={busy}
        >
          I’m looking for work
        </button>

        <button
          type="button"
          className={role === "employer" ? "selected" : ""}
          onClick={() => setRole("employer")}
          disabled={busy}
        >
          I’m hiring
        </button>
      </div>

      {role === "employer" && (
        <label>
          Organisation name
          <input
            type="text"
            value={organisationName}
            onChange={(event) => setOrganisationName(event.target.value)}
            required
            disabled={busy}
          />
        </label>
      )}

      {error && <div className="alert error">{error}</div>}

      <form className="form-stack" onSubmit={emailSignup}>
        <h2>Sign up with email</h2>

        <label>
          First name
          <input
            type="text"
            name="first_name"
            autoComplete="given-name"
            required
            disabled={busy}
          />
        </label>

        <label>
          Last name
          <input
            type="text"
            name="last_name"
            autoComplete="family-name"
            required
            disabled={busy}
          />
        </label>

        <label>
          Email address
          <input
            type="email"
            name="email"
            autoComplete="email"
            required
            disabled={busy}
          />
        </label>

        <PhoneInput />

        <label>
          Password
          <input
            type="password"
            name="password"
            autoComplete="new-password"
            minLength="8"
            required
            disabled={busy}
          />
        </label>

        <label>
          Confirm password
          <input
            type="password"
            name="confirm_password"
            autoComplete="new-password"
            minLength="8"
            required
            disabled={busy}
          />
        </label>

        <label className="consent">
          <input
            type="checkbox"
            checked={acceptedTerms}
            onChange={(event) => setAcceptedTerms(event.target.checked)}
            required
            disabled={busy}
          />

          <span>
            I accept the{" "}
            <Link to="/privacy" target="_blank" rel="noreferrer">
              Terms of Use and Privacy Notice
            </Link>
            .
          </span>
        </label>

        <button className="button primary" disabled={busy}>
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>

      <div className="auth-divider">
        <span>or</span>
      </div>

      <SocialSignInButtons
        onCredential={social}
        disabled={busy}
        label="Sign up"
      />

      <p className="onboarding-note">
        After signup, complete your contact details, professional profile or
        organisation information from your Profile page.
      </p>

      <p>
        Already registered? <Link to="/login">Sign in</Link>
      </p>

      <small className="social-safety-note">
        Social signup confirms control of the selected online account.
        Employer verification remains a separate safety check.
      </small>
    </div>
  );
}