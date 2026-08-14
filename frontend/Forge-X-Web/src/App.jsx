import React from "react";
import { BrowserRouter, Link } from "react-router-dom";
import AppRoutes from "./routes/AppRoutes";
import { environment } from "./config/environment";
import { Sparkles, Layers, Cpu, ShieldCheck, Github } from "lucide-react";

export function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        {/* Navigation Navbar */}
        <header
          style={{
            borderBottom: "1px solid var(--border-color)",
            background: "rgba(10, 13, 20, 0.8)",
            backdropFilter: "blur(12px)",
            position: "sticky",
            top: 0,
            zIndex: 100,
          }}
        >
          <div
            style={{
              maxWidth: "1500px",
              margin: "0 auto",
              padding: "14px 20px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <Link
              to="/orchestrator"
              style={{
                textDecoration: "none",
                display: "flex",
                alignItems: "center",
                gap: "10px",
              }}
            >
              <div
                style={{
                  width: "34px",
                  height: "34px",
                  borderRadius: "8px",
                  background: "linear-gradient(135deg, #6366f1, #06b6d4)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 0 12px rgba(99, 102, 241, 0.5)",
                }}
              >
                <Sparkles size={18} color="#ffffff" />
              </div>
              <div>
                <span
                  style={{
                    fontSize: "1.15rem",
                    fontWeight: "800",
                    letterSpacing: "-0.03em",
                    background: "linear-gradient(135deg, #ffffff, #94a3b8)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                  }}
                >
                  Forge-X
                </span>
                <span
                  style={{
                    marginLeft: "8px",
                    fontSize: "0.75rem",
                    color: "var(--text-muted)",
                    borderLeft: "1px solid var(--border-color)",
                    paddingLeft: "8px",
                  }}
                >
                  Dynamic Workflow Orchestrator V5
                </span>
              </div>
            </Link>

            {/* Right Status Info */}
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span
                style={{
                  fontSize: "0.75rem",
                  padding: "4px 10px",
                  borderRadius: "14px",
                  background:
                    environment.appEnvironment === "prod"
                      ? "rgba(16, 185, 129, 0.15)"
                      : environment.appEnvironment === "staging"
                      ? "rgba(245, 158, 11, 0.15)"
                      : "rgba(99, 102, 241, 0.15)",
                  color:
                    environment.appEnvironment === "prod"
                      ? "#34d399"
                      : environment.appEnvironment === "staging"
                      ? "#fbbf24"
                      : "#818cf8",
                  border: `1px solid ${
                    environment.appEnvironment === "prod"
                      ? "rgba(16, 185, 129, 0.3)"
                      : environment.appEnvironment === "staging"
                      ? "rgba(245, 158, 11, 0.3)"
                      : "rgba(99, 102, 241, 0.3)"
                  }`,
                  fontWeight: "600",
                  textTransform: "uppercase",
                }}
              >
                Env: {environment.appEnvironment}
              </span>

              <div
                style={{
                  fontSize: "0.78rem",
                  color: "var(--text-muted)",
                  fontFamily: "var(--font-mono)",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <Cpu size={14} color="#22d3ee" /> Deep Agents v5.0
              </div>
            </div>
          </div>
        </header>

        {/* Main Content View */}
        <main style={{ flex: 1 }}>
          <AppRoutes />
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
