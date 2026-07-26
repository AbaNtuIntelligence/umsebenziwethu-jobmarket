import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider } from "./state/AuthContext";
import App from "./App";
import "./styles.css";
import "./application.css";
import "./pilot.css";
import "./apply-flow.css";
import "./avatar.css";
import "./interview.css";
import "./listing-management.css";
import "./talent-directory.css";
import "./safety.css";
import "./phone-input.css";
import "./employer-logo.css";
import "./job-media-management.css";
import "./mobile-safety-navigation.css";

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const application = <BrowserRouter><AuthProvider><App /></AuthProvider></BrowserRouter>;

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    {googleClientId ? <GoogleOAuthProvider clientId={googleClientId}>{application}</GoogleOAuthProvider> : application}
  </React.StrictMode>
);
