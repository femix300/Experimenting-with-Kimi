import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../stores";

export default function ProtectedRoute() {
  const { isAuthenticated, authLoading } = useAuthStore();

  if (authLoading) return null;

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  return <Outlet />;
}
