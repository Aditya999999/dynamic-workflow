import React from "react";
import { Bot, Layers, Code, ShieldCheck, CheckCircle2, Clock, XCircle, AlertTriangle, FileText, ChevronRight, X } from "lucide-react";

export function AgentDetailsPanel({ node, onClose, onPreviewArtifact }) {
  if (!node) return null;

  return (
    <div
      className="glass-panel"
      style={{
        padding: "20px",
        marginBottom: "20px",
        border: "1px solid var(--border-active)",
        position: "relative",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "14px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <span style={{ fontSize: "0.8rem", fontWeight: "700", color: "#818cf8", textTransform: "capitalize" }}>
              {node.agent_id}
            </span>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
              ID: {node.id}
            </span>
          </div>
          <h3 style={{ fontSize: "1.05rem", fontWeight: "700" }}>{node.display_name}</h3>
        </div>

        <button
          onClick={onClose}
          style={{
            padding: "4px",
            background: "transparent",
            border: "none",
            color: "var(--text-muted)",
            cursor: "pointer",
          }}
        >
          <X size={18} />
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px", marginBottom: "16px" }}>
        <div style={{ background: "var(--bg-input)", padding: "10px 14px", borderRadius: "8px" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Status</span>
          <div style={{ fontWeight: "600", fontSize: "0.85rem", textTransform: "capitalize" }}>{node.status}</div>
        </div>
        <div style={{ background: "var(--bg-input)", padding: "10px 14px", borderRadius: "8px" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Plan Version</span>
          <div style={{ fontWeight: "600", fontSize: "0.85rem" }}>v{node.plan_version}</div>
        </div>
        <div style={{ background: "var(--bg-input)", padding: "10px 14px", borderRadius: "8px" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Invocation Count</span>
          <div style={{ fontWeight: "600", fontSize: "0.85rem" }}>{node.invocation_count}</div>
        </div>
      </div>

      {node.artifact_refs?.length > 0 && (
        <div style={{ marginBottom: "14px" }}>
          <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
            Associated Artifacts:
          </span>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {node.artifact_refs.map((artId) => (
              <button
                key={artId}
                onClick={() => onPreviewArtifact(artId)}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  background: "rgba(6, 182, 212, 0.15)",
                  color: "#22d3ee",
                  border: "1px solid rgba(6, 182, 212, 0.3)",
                  fontSize: "0.8rem",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                <FileText size={14} /> Preview {artId}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Output Data / Logs */}
      {node.output_data && Object.keys(node.output_data).length > 0 && (
        <div>
          <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
            Node Output:
          </span>
          <pre
            style={{
              background: "var(--bg-primary)",
              padding: "12px",
              borderRadius: "8px",
              fontSize: "0.78rem",
              fontFamily: "var(--font-mono)",
              color: "#94a3b8",
              maxHeight: "180px",
              overflowY: "auto",
              whiteSpace: "pre-wrap",
            }}
          >
            {JSON.stringify(node.output_data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
