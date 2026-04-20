import { Navigate } from "react-router-dom";
import { TeamAccessControl } from "../utils/TeamAccessControl";

const ProtectedRoute = ({ children }) => {
  const userEmail = localStorage.getItem("userEmail") || "";
  const isTeamMember = TeamAccessControl.isTeamMember(userEmail);
  const isAdmin = localStorage.getItem("isAdmin") === "true";

  if (!isTeamMember && !isAdmin) {
    return <Navigate to="/dashboard" />;
  }

  return children;
};

export default ProtectedRoute;