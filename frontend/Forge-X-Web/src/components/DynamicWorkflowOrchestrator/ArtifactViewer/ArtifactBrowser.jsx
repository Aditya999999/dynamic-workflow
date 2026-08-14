import React from "react";
import { FileText, Code, Layers, FileJson, ArrowUpRight } from "lucide-react";

export function ArtifactBrowser({ artifacts, onSelectArtifact }) {
  if (!artifacts || artifacts.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)", fontSize: "0.85rem" }}>
        No artifacts generated yet. Artifacts will appear here as agents complete their tasks.
      </div>
    );
  }

  const getIcon = (type) => {
    switch (type) {
      case "code":
        return <Code size={16} color="#c084fc" />;
      case "json":
        return <FileJson size={16} color="#fbbf24" />;
      default:
        return <FileText size={16} color="#22d3ee" />;
    }
  };

  return (
    <div className="glass-panel" style={{ padding: "20px" }}>
      <h3 style={{ fontSize: "1rem", fontWeight: "700", marginBottom: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
        <Layers size={18} color="#22d3ee" /> Generated Artifacts ({artifacts.length})
      </h3>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "12px" }}>
        {artifacts.map((art) => (
          <div
            key={art.artifact_id}
            onClick={() => onSelectArtifact(art.artifact_id)}
            className="glow-hover"
            style={{
              padding: "14px",
              borderRadius: "10px",
              background: "var(--bg-input)",
              border: "1px solid var(--border-color)",
              cursor: "pointer",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  {getIcon(art.artifact_type)}
                  <span style={{ fontWeight: "600", fontSize: "0.85rem", color: "var(--text-primary)" }}>
                    {art.name}
                  </span>
                </div>
                <ArrowUpRight size={14} color="var(--text-muted)" />
              </div>

              {art.summary && (
                <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", lineHeight: "1.4", marginBottom: "8px" }}>
                  {art.summary}
                </p>
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.7rem", color: "var(--text-muted)" }}>
              <span style={{ fontFamily: "var(--font-mono)" }}>{art.artifact_id}</span>
              {art.size_bytes > 0 && <span>{(art.size_bytes / 1024).toFixed(1)} KB</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
