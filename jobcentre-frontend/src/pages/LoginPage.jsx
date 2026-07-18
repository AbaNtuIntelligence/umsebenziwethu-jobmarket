import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { errorMessage } from "../services/api";
import { useAuth } from "../state/AuthContext";
export default function LoginPage() {
  const {login} = useAuth(); const navigate = useNavigate(); const location = useLocation(); const [error, setError] = useState("");
  async function submit(e) { e.preventDefault(); const data = Object.fromEntries(new FormData(e.currentTarget)); try { const user = await login(data.email, data.password); navigate(location.state?.from?.pathname || (user.role === "employer" ? "/employer" : "/")); } catch(e) { setError(errorMessage(e)); } }
  return <div className="auth-card"><h1>Welcome back</h1><p>Log in to continue to Job Centre.</p>{error && <div className="alert error">{error}</div>}<form onSubmit={submit} className="form-stack"><label>Email<input type="email" name="email" required/></label><label>Password<input type="password" name="password" required/></label><Link to="/forgot-password">Forgot your password?</Link><button className="button primary">Log in</button></form><p>New here? <Link to="/register">Create an account</Link></p></div>;
}
