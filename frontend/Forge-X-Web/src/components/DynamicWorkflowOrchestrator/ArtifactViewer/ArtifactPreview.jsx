import React, { useState, useEffect } from "react";
import { FileText, Copy, Check, X, Download, Code, Layers, Sparkles } from "lucide-react";
import orchestratorApi from "../../../services/orchestratorApi";

export function ArtifactPreview({ workflowId, artifactId, onClose }) {
  const [artifactData, setArtifactData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!workflowId || !artifactId) return;

    let isMounted = true;
    setLoading(true);

    orchestratorApi
      .getArtifact(workflowId, artifactId)
      .then((data) => {
        if (isMounted) {
          setArtifactData(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.response?.data?.message || err.message);
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [workflowId, artifactId]);

  const handleCopy = () => {
    if (!artifactData?.content) return;
    navigator.clipboard.writeText(artifactData.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        bottom: 0,
        width: "min(650px, 90vw)",
        background: "var(--bg-secondary)",
        borderLeft: "1px solid var(--border-color)",
        boxShadow: "-10px 0 30px rgba(0, 0, 0, 0.7)",
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
        animation: "slideLeft 0.3s ease-out",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "16px 20px",
          borderBottom: "1px solid var(--border-color)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "var(--bg-input)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <FileText size={20} color="#22d3ee" />
          <div>
            <h3 style={{ fontSize: "0.95rem", fontWeight: "700", color: "var(--text-primary)" }}>
              {artifactData?.metadata?.name || "Artifact Preview"}
            </h3>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
              {artifactId}
            </span>
          </div>
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <button
            onClick={handleCopy}
            disabled={!artifactData?.content}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              padding: "6px 10px",
              borderRadius: "6px",
              background: "rgba(255, 255, 255, 0.05)",
              color: copied ? "#34d399" : "var(--text-secondary)",
              border: "1px solid var(--border-color)",
              fontSize: "0.75rem",
              cursor: "pointer",
            }}
          >
            {copied ? <Check size={13} /> : <Copy size={13} />} {copied ? "Copied" : "Copy"}
          </button>

          <button
            onClick={onClose}
            style={{
              padding: "6px",
              borderRadius: "6px",
              background: "transparent",
              color: "var(--text-muted)",
              border: "none",
              cursor: "pointer",
            }}
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Body Content */}
      <div style={{ flex: 1, overflowY: "auto", padding: "20px" }}>
        {loading && (
          <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-muted)" }}>
            Loading artifact content...
          </div>
        )}

        {error && (
          <div style={{ color: "#fb7185", background: "rgba(244, 63, 94, 0.1)", padding: "14px", borderRadius: "8px" }}>
            Failed to load artifact: {error}
          </div>
        )}

        {artifactData && !loading && (
          <div>
            {artifactData.metadata?.summary && (
              <div
                style={{
                  background: "rgba(6, 182, 212, 0.08)",
                  border: "1px solid rgba(6, 182, 212, 0.2)",
                  borderRadius: "8px",
                  padding: "12px 16px",
                  fontSize: "0.82rem",
                  color: "#22d3ee",
                  marginBottom: "16px",
                }}
              >
                <strong>Summary: </strong> {artifactData.metadata.summary}
              </div>
            )}

            <pre
              style={{
                background: "var(--bg-primary)",
                border: "1px solid var(--border-color)",
                borderRadius: "10px",
                padding: "16px",
                fontFamily: "var(--font-mono)",
                fontSize: "0.82rem",
                color: "#e2e8f0",
                lineHeight: "1.6",
                whiteSpace: "pre-wrap",
                overflowX: "auto",
              }}
            >
              {artifactData.content}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
