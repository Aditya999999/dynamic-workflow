import React, { useState } from "react";
import { Sparkles, Play, ArrowRight, Layers, Bot, ShieldCheck, Code, FileText, CheckCircle2 } from "lucide-react";

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

export function QueryInput({ onPlanWorkflow, loading }) {
  const [query, setQuery] = useState("");
  const [selectedPreset, setSelectedPreset] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return;
    onPlanWorkflow(query);
  };

  const handleSelectPreset = (preset) => {
    setSelectedPreset(preset.title);
    setQuery(preset.query);
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

      <form onSubmit={handleSubmit}>
        <div style={{ position: "relative", marginBottom: "16px" }}>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Describe the workflow you want the agents to execute..."
            rows={4}
            style={{
              width: "100%",
              padding: "16px",
              borderRadius: "12px",
              background: "var(--bg-input)",
              border: "1px solid var(--border-color)",
              color: "var(--text-primary)",
              fontFamily: "var(--font-sans)",
              fontSize: "0.95rem",
              resize: "vertical",
              outline: "none",
              transition: "border-color 0.2s",
            }}
            onFocus={(e) => (e.target.style.borderColor = "var(--primary)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border-color)")}
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
