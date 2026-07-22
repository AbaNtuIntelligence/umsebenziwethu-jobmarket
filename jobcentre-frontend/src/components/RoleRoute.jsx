import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../state/AuthContext";

export default function RoleRoute({ allowedRoles }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <div className="card empty">Checking your account…</div>;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  if (!allowedRoles.includes(user.role)) {
    return <Navigate to={user.role === "employer" ? "/employer" : "/"} replace />;
  }
  return <Outlet />;
}
