import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import { AdminAuthProvider } from "./auth/AdminAuthContext.jsx";
import ProtectedRoute from "./auth/ProtectedRoute.jsx";
import "./index.css";
import "./styles/admin-auth.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AdminAuthProvider>
      <ProtectedRoute>
        <App />
      </ProtectedRoute>
    </AdminAuthProvider>
  </React.StrictMode>
);
