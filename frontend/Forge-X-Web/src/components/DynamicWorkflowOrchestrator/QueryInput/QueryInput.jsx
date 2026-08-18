import React, { useState } from "react";
import { Sparkles, ArrowRight, Layers, Bot, ShieldCheck, Code, AlertTriangle, X, Lightbulb } from "lucide-react";

const PRESETS = [
  {
    title: "End-to-End SDLC Pipeline",
    desc: "BRD -> Architecture -> Dev Scaffolding -> QE Strategy",
    query: "Create a BRD for an online payment platform, design the architecture, prepare implementation tasks, and create a QA strategy.",
  },
  {
    title: "Dynamic Clarification Flow",
    desc: "Triggers Architect -> BA revision loop",
    query: "Design an enterprise reconciliation platform with dynamic settlement windows and automated webhook retries.",
  },
  {
    title: "Human-In-The-Loop Approval",
    desc: "Requires human signoff on business requirements",
    query: "Generate a detailed BRD for cloud migration requiring compliance team signoff.",
  },
];

const SUGGESTED_QUERIES = [
  "Create a BRD and Architecture for an online payment gateway",
  "Design microservices and generate C4 diagrams for e-commerce checkout",
  "Implement FastAPI service endpoints for authentication and user management",
  "Generate test strategy and pytest automation suite for order processing"
];

export function QueryInput({ onPlanWorkflow, loading, errorMessage, onClearError }) {
  const [query, setQuery] = useState("");
  const [selectedPreset, setSelectedPreset] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return;
    onPlanWorkflow(query);
  };

  const handleSelectPreset = (preset) => {
    if (onClearError) onClearError();
    setSelectedPreset(preset.title);
    setQuery(preset.query);
  };

  const handleSelectSuggestion = (suggestion) => {
    if (onClearError) onClearError();
    setSelectedPreset(null);
    setQuery(suggestion);
  };

  const handleQueryChange = (e) => {
    if (errorMessage && onClearError) {
      onClearError();
    }
    setQuery(e.target.value);
  };

  return (
    <div className="glass-panel" style={{ padding: "32px", maxWidth: "900px", margin: "0 auto" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
        <div style={{
          width: "40px",
          height: "40px",
          borderRadius: "10px",
          background: "linear-gradient(135deg, #6366f1, #06b6d4)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 0 15px rgba(99, 102, 241, 0.4)"
        }}>
          <Sparkles size={22} color="#ffffff" />
        </div>
        <div>
          <h2 style={{ fontSize: "1.4rem", fontWeight: "700", letterSpacing: "-0.02em" }}>
            Dynamic Workflow Orchestrator
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            State-of-the-art multi-agent planning & execution powered by Deep Agents
          </p>
        </div>
      </div>

      {/* Preset Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "12px", marginBottom: "20px" }}>
        {PRESETS.map((p) => (
          <div
            key={p.title}
            onClick={() => handleSelectPreset(p)}
            className="glow-hover"
            style={{
              padding: "14px",
              borderRadius: "10px",
              background: selectedPreset === p.title ? "var(--bg-input)" : "rgba(255, 255, 255, 0.03)",
              border: selectedPreset === p.title ? "1px solid var(--primary)" : "1px solid var(--border-color)",
              cursor: "pointer",
            }}
          >
            <div style={{ fontWeight: "600", fontSize: "0.85rem", color: selectedPreset === p.title ? "var(--primary)" : "var(--text-primary)", marginBottom: "4px" }}>
              {p.title}
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
              {p.desc}
            </div>
          </div>
        ))}
      </div>

      {/* Custom Error / Out-of-Scope Banner */}
      {errorMessage && (
        <div
          style={{
            marginBottom: "20px",
            padding: "16px 20px",
            borderRadius: "12px",
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.4)",
            boxShadow: "0 4px 20px rgba(239, 68, 68, 0.15)",
            animation: "fadeIn 0.25s ease-out",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px" }}>
            <div style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
              <div style={{
                padding: "6px",
                borderRadius: "8px",
                background: "rgba(239, 68, 68, 0.2)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0
              }}>
                <AlertTriangle size={20} color="#ef4444" />
              </div>
              <div>
                <div style={{ fontWeight: "700", color: "#f87171", fontSize: "0.95rem", marginBottom: "4px" }}>
                  SDLC Scope Notice
                </div>
                <div style={{ color: "var(--text-primary)", fontSize: "0.88rem", lineHeight: "1.5" }}>
                  {errorMessage}
                </div>
                
                {/* Suggestions */}
                <div style={{ marginTop: "12px" }}>
                  <div style={{ fontSize: "0.78rem", fontWeight: "600", color: "var(--text-secondary)", marginBottom: "6px", display: "flex", alignItems: "center", gap: "5px" }}>
                    <Lightbulb size={13} color="#f59e0b" /> Try asking for an SDLC requirement instead:
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {SUGGESTED_QUERIES.map((sq, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => handleSelectSuggestion(sq)}
                        style={{
                          background: "rgba(255, 255, 255, 0.06)",
                          border: "1px solid rgba(255, 255, 255, 0.12)",
                          color: "var(--text-primary)",
                          padding: "4px 10px",
                          borderRadius: "16px",
                          fontSize: "0.75rem",
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = "rgba(99, 102, 241, 0.2)";
                          e.currentTarget.style.borderColor = "var(--primary)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = "rgba(255, 255, 255, 0.06)";
                          e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.12)";
                        }}
                      >
                        {sq}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            {onClearError && (
              <button
                type="button"
                onClick={onClearError}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                  padding: "4px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
                title="Dismiss"
              >
                <X size={16} />
              </button>
            )}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ position: "relative", marginBottom: "16px" }}>
          <textarea
            value={query}
            onChange={handleQueryChange}
            placeholder="Describe the workflow you want the agents to execute..."
            rows={4}
            style={{
              width: "100%",
              padding: "16px",
              borderRadius: "12px",
              background: "var(--bg-input)",
              border: errorMessage ? "1px solid #ef4444" : "1px solid var(--border-color)",
              color: "var(--text-primary)",
              fontFamily: "var(--font-sans)",
              fontSize: "0.95rem",
              resize: "vertical",
              outline: "none",
              transition: "border-color 0.2s",
            }}
            onFocus={(e) => (e.target.style.borderColor = errorMessage ? "#ef4444" : "var(--primary)")}
            onBlur={(e) => (e.target.style.borderColor = errorMessage ? "#ef4444" : "var(--border-color)")}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <span style={{ display: "inline-flex", alignItems: "center", gap: "5px", padding: "4px 10px", borderRadius: "20px", background: "rgba(99, 102, 241, 0.1)", color: "#818cf8", fontSize: "0.75rem" }}>
              <Bot size={13} /> BA Agent
            </span>
            <span style={{ display: "inline-flex", alignItems: "center", gap: "5px", padding: "4px 10px", borderRadius: "20px", background: "rgba(6, 182, 212, 0.1)", color: "#22d3ee", fontSize: "0.75rem" }}>
              <Layers size={13} /> Architect
            </span>
            <span style={{ display: "inline-flex", alignItems: "center", gap: "5px", padding: "4px 10px", borderRadius: "20px", background: "rgba(168, 85, 247, 0.1)", color: "#c084fc", fontSize: "0.75rem" }}>
              <Code size={13} /> Developer
            </span>
            <span style={{ display: "inline-flex", alignItems: "center", gap: "5px", padding: "4px 10px", borderRadius: "20px", background: "rgba(16, 185, 129, 0.1)", color: "#34d399", fontSize: "0.75rem" }}>
              <ShieldCheck size={13} /> QE Agent
            </span>
          </div>

          <button
            type="submit"
            disabled={!query.trim() || loading}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              padding: "12px 24px",
              borderRadius: "10px",
              background: query.trim() ? "linear-gradient(135deg, #6366f1, #4f46e5)" : "var(--bg-input)",
              color: query.trim() ? "#ffffff" : "var(--text-muted)",
              border: "none",
              fontWeight: "600",
              fontSize: "0.95rem",
              cursor: query.trim() && !loading ? "pointer" : "not-allowed",
              boxShadow: query.trim() ? "0 4px 15px rgba(99, 102, 241, 0.4)" : "none",
              transition: "all 0.2s",
            }}
          >
            {loading ? (
              <>Planning Workflow...</>
            ) : (
              <>
                Generate Plan <ArrowRight size={17} />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
