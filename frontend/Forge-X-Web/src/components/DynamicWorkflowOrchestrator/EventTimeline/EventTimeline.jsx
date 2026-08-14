import React, { useRef, useEffect } from "react";
import { Activity, Clock, CheckCircle2, AlertTriangle, FileText, GitBranch, XCircle, Bot } from "lucide-react";

export function EventTimeline({ events, isConnected }) {
  const listEndRef = useRef(null);

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  const getEventBadge = (type) => {
    switch (type) {
      case "node_started":
        return { color: "#818cf8", bg: "rgba(99, 102, 241, 0.15)", icon: Clock, label: "Node Started" };
      case "node_completed":
        return { color: "#34d399", bg: "rgba(16, 185, 129, 0.15)", icon: CheckCircle2, label: "Node Completed" };
      case "artifact_written":
        return { color: "#22d3ee", bg: "rgba(6, 182, 212, 0.15)", icon: FileText, label: "Artifact Written" };
      case "plan_updated":
        return { color: "#c084fc", bg: "rgba(168, 85, 247, 0.15)", icon: GitBranch, label: "Plan Updated" };
      case "interrupt_requested":
        return { color: "#fbbf24", bg: "rgba(245, 158, 11, 0.15)", icon: AlertTriangle, label: "HITL Requested" };
      case "hitl_resolved":
        return { color: "#34d399", bg: "rgba(16, 185, 129, 0.15)", icon: CheckCircle2, label: "HITL Resolved" };
      case "workflow_completed":
        return { color: "#34d399", bg: "rgba(16, 185, 129, 0.2)", icon: CheckCircle2, label: "Workflow Completed" };
      case "workflow_failed":
      case "node_failed":
        return { color: "#fb7185", bg: "rgba(244, 63, 94, 0.15)", icon: XCircle, label: "Failed" };
      default:
        return { color: "#94a3b8", bg: "rgba(148, 163, 184, 0.15)", icon: Activity, label: type };
    }
  };

  return (
    <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
        <h3 style={{ fontSize: "1rem", fontWeight: "700", display: "flex", alignItems: "center", gap: "8px" }}>
          <Activity size={18} color="#6366f1" /> Live Event Timeline
        </h3>

        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.75rem" }}>
          <div
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: isConnected ? "#10b981" : "#f43f5e",
              boxShadow: isConnected ? "0 0 8px #10b981" : "none",
            }}
          />
          <span style={{ color: isConnected ? "#34d399" : "var(--text-muted)" }}>
            {isConnected ? "Stream Connected" : "Connecting..."}
          </span>
        </div>
      </div>

      <div
        style={{
          flex: 1,
          maxHeight: "360px",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          paddingRight: "6px",
        }}
      >
        {(!events || events.length === 0) && (
          <div style={{ textAlign: "center", padding: "30px 0", color: "var(--text-muted)", fontSize: "0.85rem" }}>
            Waiting for execution events...
          </div>
        )}

        {events?.map((ev, index) => {
          const badge = getEventBadge(ev.event_type);
          const EventIcon = badge.icon;
          const timeStr = ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : "";

          return (
            <div
              key={`${ev.sequence_number}-${index}`}
              style={{
                background: "var(--bg-input)",
                border: "1px solid var(--border-color)",
                borderRadius: "8px",
                padding: "10px 12px",
                display: "flex",
                gap: "10px",
                alignItems: "flex-start",
                fontSize: "0.82rem",
              }}
            >
              <div
                style={{
                  width: "24px",
                  height: "24px",
                  borderRadius: "6px",
                  background: badge.bg,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  marginTop: "2px",
                }}
              >
                <EventIcon size={14} color={badge.color} />
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2px" }}>
                  <span style={{ fontWeight: "700", color: badge.color }}>{badge.label}</span>
                  <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                    #{ev.sequence_number} {timeStr}
                  </span>
                </div>

                {ev.agent_id && (
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    Agent: <strong style={{ color: "var(--text-primary)" }}>{ev.agent_id}</strong>
                    {ev.node_id && <span> ({ev.node_id})</span>}
                  </div>
                )}

                {ev.payload?.reason && (
                  <div style={{ fontSize: "0.75rem", color: "#fbbf24", marginTop: "2px" }}>
                    {ev.payload.reason}
                  </div>
                )}
                {ev.payload?.name && (
                  <div style={{ fontSize: "0.75rem", color: "#22d3ee", marginTop: "2px" }}>
                    {ev.payload.name}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        <div ref={listEndRef} />
      </div>
    </div>
  );
}
