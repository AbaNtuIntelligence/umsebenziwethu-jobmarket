import { FileText } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { errorMessage } from "../services/api";

export default function RegisterPage() {
  const [role, setRole] = useState("job_seeker");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [resumeName, setResumeName] = useState("");
  const navigate = useNavigate();

  async function submit(event) {
    event.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api.post("/auth/register/", new FormData(event.currentTarget));
      navigate("/login", { state: { registered: true } });
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setSaving(false);
    }
  }

  return <div className="auth-card wide">
    <h1>Build your opportunity profile</h1>
    <p>Join the controlled UmsebenziWethu pilot as a job seeker or employer.</p>
    <div className="role-picker">
      <button type="button" className={role === "job_seeker" ? "selected" : ""} onClick={() => setRole("job_seeker")}>I’m looking for work</button>
      <button type="button" className={role === "employer" ? "selected" : ""} onClick={() => setRole("employer")}>I’m hiring</button>
    </div>
    {error && <div className="alert error">{error}</div>}
    <form onSubmit={submit} className="form-grid">
      <input type="hidden" name="role" value={role} />
      <label>First name<input name="first_name" required /></label>
      <label>Last name<input name="last_name" required /></label>
      <label>Username<input name="username" required /></label>
      <label>Email<input type="email" name="email" required /></label>
      <label>Phone number<input type="tel" name="phone" /></label>

      {role === "employer" ? (
        <label className="span-2">Organisation name<input name="organisation_name" required /></label>
      ) : (
        <>
          <label className="span-2">Professional headline<input name="professional_headline" placeholder="e.g. Junior IT Support Technician" /></label>
          <label>Province<input name="province" placeholder="Gauteng" /></label>
          <label>City or town<input name="city" placeholder="Johannesburg" /></label>
          <label className="span-2">Skills<input name="skills" placeholder="Technical support, driving, customer service" /></label>
          <label>Availability<input name="availability" placeholder="Immediately available" /></label>
          <label className="resume-upload span-2">
            <FileText />
            <span><b>Upload résumé or CV</b><small>{resumeName || "PDF only, maximum 5 MB"}</small></span>
            <input
              type="file"
              name="resume"
              accept="application/pdf,.pdf"
              onChange={(event) => setResumeName(event.target.files?.[0]?.name || "")}
            />
          </label>
        </>
      )}

      <label className="span-2">Pilot invitation code<input name="invite_code" autoComplete="off" placeholder="Provided with your invitation" /></label>
      <label className="span-2">Password<input type="password" name="password" minLength="8" required /></label>
      <label className="consent span-2"><input type="checkbox" name="accept_terms" value="true" required /><span>I accept the <Link to="/privacy" target="_blank">Terms of Use and Privacy Notice</Link>.</span></label>
      <button className="button primary span-2" disabled={saving}>{saving ? "Creating profile…" : "Create account"}</button>
    </form>
    <p>Already registered? <Link to="/login">Log in</Link></p>
  </div>;
}
