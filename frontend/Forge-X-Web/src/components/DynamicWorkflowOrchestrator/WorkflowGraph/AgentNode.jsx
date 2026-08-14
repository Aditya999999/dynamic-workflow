import React, { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { Bot, Layers, Code, ShieldCheck, CheckCircle2, Clock, AlertTriangle, XCircle, FileText } from "lucide-react";

const AGENT_CONFIGS = {
  "business-analyst": { icon: Bot, color: "#818cf8", bg: "rgba(99, 102, 241, 0.12)", border: "#6366f1" },
  architect: { icon: Layers, color: "#22d3ee", bg: "rgba(6, 182, 212, 0.12)", border: "#06b6d4" },
  developer: { icon: Code, color: "#c084fc", bg: "rgba(168, 85, 247, 0.12)", border: "#a855f7" },
  "product-owner": { icon: Bot, color: "#fbbf24", bg: "rgba(245, 158, 11, 0.12)", border: "#f59e0b" },
  qe: { icon: ShieldCheck, color: "#34d399", bg: "rgba(16, 185, 129, 0.12)", border: "#10b981" },
};

export const AgentNode = memo(({ data, selected }) => {
  const agentCfg = AGENT_CONFIGS[data.agent_id] || AGENT_CONFIGS["business-analyst"];
  const AgentIcon = agentCfg.icon;

  const isExecuting = data.status === "executing";
  const isCompleted = data.status === "completed";
  const isAwaiting = data.status === "awaiting_approval";
  const isFailed = data.status === "failed";

  const getStatusBorder = () => {
    if (isExecuting) return "#6366f1";
    if (isCompleted) return "#10b981";
    if (isAwaiting) return "#f59e0b";
    if (isFailed) return "#f43f5e";
    return selected ? "#818cf8" : "rgba(255, 255, 255, 0.12)";
  };

  return (
    <div
      style={{
        minWidth: "240px",
        padding: "14px 16px",
        borderRadius: "14px",
        background: isExecuting ? "rgba(30, 41, 75, 0.95)" : "rgba(17, 24, 39, 0.9)",
        border: `2px solid ${getStatusBorder()}`,
        boxShadow: isExecuting
          ? "0 0 25px rgba(99, 102, 241, 0.5)"
          : isAwaiting
          ? "0 0 20px rgba(245, 158, 11, 0.4)"
          : selected
          ? "0 0 15px rgba(99, 102, 241, 0.3)"
          : "0 4px 15px rgba(0, 0, 0, 0.5)",
        backdropFilter: "blur(12px)",
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        cursor: "pointer",
        position: "relative",
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: agentCfg.border, width: 10, height: 10 }} />

      {/* Header with Icon and Version Pill */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "8px",
              background: agentCfg.bg,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <AgentIcon size={16} color={agentCfg.color} />
          </div>
          <span style={{ fontSize: "0.8rem", fontWeight: "700", color: agentCfg.color, textTransform: "capitalize" }}>
            {data.agent_id.replace("-", " ")}
          </span>
        </div>

        {data.plan_version > 1 && (
          <span
            style={{
              fontSize: "0.65rem",
              background: "rgba(168, 85, 247, 0.2)",
              color: "#c084fc",
              padding: "1px 6px",
              borderRadius: "10px",
              fontWeight: "600",
            }}
          >
            v{data.plan_version}
          </span>
        )}
      </div>

      {/* Task Name */}
      <div
        style={{
          fontSize: "0.88rem",
          fontWeight: "600",
          color: "var(--text-primary)",
          marginBottom: "10px",
          lineHeight: "1.3",
        }}
      >
        {data.label}
      </div>

      {/* Status Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.75rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
          {isExecuting && (
            <span style={{ color: "#818cf8", display: "flex", alignItems: "center", gap: "4px" }}>
              <Clock size={13} className="animate-spin" /> Executing...
            </span>
          )}
          {isCompleted && (
            <span style={{ color: "#34d399", display: "flex", alignItems: "center", gap: "4px" }}>
              <CheckCircle2 size={13} /> Completed
            </span>
          )}
          {isAwaiting && (
            <span style={{ color: "#fbbf24", display: "flex", alignItems: "center", gap: "4px" }}>
              <AlertTriangle size={13} /> Review Required
            </span>
          )}
          {isFailed && (
            <span style={{ color: "#fb7185", display: "flex", alignItems: "center", gap: "4px" }}>
              <XCircle size={13} /> Failed
            </span>
          )}
          {data.status === "planned" && (
            <span style={{ color: "var(--text-muted)" }}>Planned</span>
          )}
          {data.status === "ready" && (
            <span style={{ color: "#22d3ee" }}>Ready</span>
          )}
        </div>

        {data.artifact_id && (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "3px",
              background: "rgba(6, 182, 212, 0.15)",
              color: "#22d3ee",
              padding: "2px 6px",
              borderRadius: "6px",
              fontSize: "0.7rem",
            }}
          >
            <FileText size={11} /> Artifact
          </span>
        )}
      </div>

      <Handle type="source" position={Position.Right} style={{ background: agentCfg.border, width: 10, height: 10 }} />
    </div>
  );
});
