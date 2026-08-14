import React from "react";
import { Play, RotateCcw, AlertTriangle, CheckCircle2, Clock, XCircle, FileText, Cpu, GitBranch } from "lucide-react";

export function PlanSummary({ workflow, onExecute, onCancel, executing }) {
  if (!workflow) return null;

  const getStatusBadge = (status) => {
    switch (status) {
      case "completed":
        return { bg: "rgba(16, 185, 129, 0.15)", border: "#10b981", color: "#34d399", icon: CheckCircle2, label: "Completed" };
      case "executing":
        return { bg: "rgba(99, 102, 241, 0.15)", border: "#6366f1", color: "#818cf8", icon: Clock, label: "Executing" };
      case "awaiting_approval":
        return { bg: "rgba(245, 158, 11, 0.15)", border: "#f59e0b", color: "#fbbf24", icon: AlertTriangle, label: "Awaiting Approval" };
      case "failed":
        return { bg: "rgba(244, 63, 94, 0.15)", border: "#f43f5e", color: "#fb7185", icon: XCircle, label: "Failed" };
      case "cancelled":
        return { bg: "rgba(100, 116, 139, 0.15)", border: "#64748b", color: "#94a3b8", icon: XCircle, label: "Cancelled" };
      default:
        return { bg: "rgba(6, 182, 212, 0.15)", border: "#06b6d4", color: "#22d3ee", icon: Cpu, label: "Planned (Ready)" };
    }
  };

  const badge = getStatusBadge(workflow.status);
  const StatusIcon = badge.icon;

  return (
    <div className="glass-panel" style={{ padding: "20px 24px", marginBottom: "20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div style={{ flex: "1 1 500px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.8rem",
                color: "var(--text-muted)",
                background: "var(--bg-input)",
                padding: "2px 8px",
                borderRadius: "6px",
              }}
            >
              {workflow.workflow_id}
            </span>

            {/* Status Pill */}
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                padding: "3px 10px",
                borderRadius: "20px",
                background: badge.bg,
                border: `1px solid ${badge.border}`,
                color: badge.color,
                fontSize: "0.8rem",
                fontWeight: "600",
              }}
            >
              <StatusIcon size={14} /> {badge.label}
            </span>

            {/* Plan Version Pill */}
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                padding: "3px 8px",
                borderRadius: "20px",
                background: "rgba(168, 85, 247, 0.15)",
                border: "1px solid #a855f7",
                color: "#c084fc",
                fontSize: "0.75rem",
                fontWeight: "600",
              }}
            >
              <GitBranch size={13} /> Plan v{workflow.plan_version}
            </span>

            {workflow.replan_count > 0 && (
              <span
                style={{
                  padding: "3px 8px",
                  borderRadius: "20px",
                  background: "rgba(245, 158, 11, 0.15)",
                  color: "#fbbf24",
                  fontSize: "0.75rem",
                }}
              >
                {workflow.replan_count} Dynamic Replan{workflow.replan_count > 1 ? "s" : ""}
              </span>
            )}
          </div>

          <h3 style={{ fontSize: "1.1rem", fontWeight: "600", color: "var(--text-primary)", lineHeight: "1.4" }}>
            {workflow.query}
          </h3>
        </div>

        {/* Action Buttons */}
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          {workflow.status === "planned" && (
            <button
              onClick={() => onExecute(false)}
              disabled={executing}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                padding: "10px 20px",
                borderRadius: "8px",
                background: "linear-gradient(135deg, #10b981, #059669)",
                color: "#ffffff",
                border: "none",
                fontWeight: "600",
                fontSize: "0.9rem",
                cursor: executing ? "not-allowed" : "pointer",
                boxShadow: "0 4px 12px rgba(16, 185, 129, 0.3)",
              }}
            >
              <Play size={16} /> Start Execution
            </button>
          )}

          {workflow.status === "executing" && (
            <button
              onClick={onCancel}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 16px",
                borderRadius: "8px",
                background: "rgba(244, 63, 94, 0.15)",
                color: "#fb7185",
                border: "1px solid #f43f5e",
                fontWeight: "600",
                fontSize: "0.85rem",
                cursor: "pointer",
              }}
            >
              <XCircle size={15} /> Cancel Workflow
            </button>
          )}
        </div>
      </div>

      {/* Metrics Bar */}
      <div
        style={{
          display: "flex",
          gap: "24px",
          marginTop: "16px",
          paddingTop: "14px",
          borderTop: "1px solid var(--border-color)",
          fontSize: "0.85rem",
          color: "var(--text-secondary)",
          flexWrap: "wrap",
        }}
      >
        <div>
          <span style={{ color: "var(--text-muted)" }}>Total Nodes: </span>
          <strong style={{ color: "var(--text-primary)" }}>{workflow.nodes?.length || 0}</strong>
        </div>
        <div>
          <span style={{ color: "var(--text-muted)" }}>Completed: </span>
          <strong style={{ color: "#34d399" }}>
            {workflow.nodes?.filter((n) => n.status === "completed").length || 0}
          </strong>
        </div>
        <div>
          <span style={{ color: "var(--text-muted)" }}>Artifacts Generated: </span>
          <strong style={{ color: "#22d3ee" }}>{workflow.artifacts?.length || 0}</strong>
        </div>
        <div>
          <span style={{ color: "var(--text-muted)" }}>Agent Invocations: </span>
          <strong style={{ color: "var(--text-primary)" }}>{workflow.total_agent_invocations || 0}</strong>
        </div>
      </div>
    </div>
  );
}
