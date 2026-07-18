import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
export default function ProtectedRoute() {
  const {user, loading} = useAuth(); const location = useLocation();
  if (loading) return <div className="card empty">Checking your account…</div>;
  return user ? <Outlet /> : <Navigate to="/login" state={{from: location}} replace />;
}
