import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./state/AuthContext";
import App from "./App";
import "./styles.css";
import "./application.css";
import "./pilot.css";
import "./apply-flow.css";
import "./avatar.css";
import "./interview.css";
import "./listing-management.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode><BrowserRouter><AuthProvider><App /></AuthProvider></BrowserRouter></React.StrictMode>
);
