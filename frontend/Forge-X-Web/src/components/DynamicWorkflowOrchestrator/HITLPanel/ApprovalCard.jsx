import React, { useState } from "react";
import { AlertTriangle, Check, Edit3, X, FileText, Send } from "lucide-react";

export function ApprovalCard({ pendingApproval, onResolve, onPreviewArtifact }) {
  const [feedback, setFeedback] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [editedJson, setEditedJson] = useState(
    JSON.stringify(pendingApproval.proposed_output || {}, null, 2)
  );

  if (!pendingApproval) return null;

  const handleApprove = () => {
    onResolve({
      decision: "approved",
      feedback: feedback || "Approved by user",
    });
  };

  const handleEditSubmit = () => {
    try {
      const parsed = JSON.parse(editedJson);
      onResolve({
        decision: "edited",
        feedback: feedback || "Edited by user",
        edited_data: parsed,
      });
    } catch (e) {
      alert("Invalid JSON format in edit payload.");
    }
  };

  const handleReject = () => {
    if (!feedback.trim()) {
      alert("Please provide a reason for rejecting in the feedback box.");
      return;
    }
    onResolve({
      decision: "rejected",
      feedback,
    });
  };

  return (
    <div
      style={{
        background: "linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(17, 24, 39, 0.95))",
        border: "1px solid #f59e0b",
        borderRadius: "14px",
        padding: "20px 24px",
        marginBottom: "20px",
        boxShadow: "0 0 25px rgba(245, 158, 11, 0.2)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
        <div
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "8px",
            background: "rgba(245, 158, 11, 0.2)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <AlertTriangle size={18} color="#fbbf24" />
        </div>
        <div>
          <h3 style={{ fontSize: "1rem", fontWeight: "700", color: "#fbbf24" }}>
            Human Approval Required (HITL)
          </h3>
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
            Agent <strong>{pendingApproval.agent_id}</strong> requested signoff before proceeding.
          </p>
        </div>
      </div>

      {/* Reason Box */}
      <div
        style={{
          background: "var(--bg-input)",
          padding: "12px 16px",
          borderRadius: "8px",
          marginBottom: "14px",
          fontSize: "0.88rem",
          color: "var(--text-primary)",
          borderLeft: "4px solid #f59e0b",
        }}
      >
        <strong>Reason: </strong> {pendingApproval.reason}
      </div>

      {/* Artifact Link if available */}
      {pendingApproval.artifact_id && (
        <div style={{ marginBottom: "14px" }}>
          <button
            onClick={() => onPreviewArtifact(pendingApproval.artifact_id)}
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
            <FileText size={14} /> Preview Generated Artifact ({pendingApproval.artifact_id})
          </button>
        </div>
      )}

      {/* Edit Mode JSON */}
      {isEditing && (
        <div style={{ marginBottom: "14px" }}>
          <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
            Edit Output Payload (JSON):
          </label>
          <textarea
            value={editedJson}
            onChange={(e) => setEditedJson(e.target.value)}
            rows={6}
            style={{
              width: "100%",
              padding: "10px",
              borderRadius: "8px",
              background: "#0d1117",
              color: "#58a6ff",
              fontFamily: "var(--font-mono)",
              fontSize: "0.8rem",
              border: "1px solid var(--border-color)",
              outline: "none",
            }}
          />
        </div>
      )}

      {/* Feedback input */}
      <div style={{ marginBottom: "16px" }}>
        <input
          type="text"
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Optional feedback or revision notes for the agents..."
          style={{
            width: "100%",
            padding: "10px 14px",
            borderRadius: "8px",
            background: "var(--bg-input)",
            border: "1px solid var(--border-color)",
            color: "var(--text-primary)",
            fontSize: "0.85rem",
            outline: "none",
          }}
        />
      </div>

      {/* Actions */}
      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
        {!isEditing ? (
          <>
            <button
              onClick={handleApprove}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "9px 18px",
                borderRadius: "8px",
                background: "#10b981",
                color: "#ffffff",
                border: "none",
                fontWeight: "600",
                fontSize: "0.85rem",
                cursor: "pointer",
              }}
            >
              <Check size={16} /> Approve & Continue
            </button>

            <button
              onClick={() => setIsEditing(true)}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "9px 18px",
                borderRadius: "8px",
                background: "rgba(255, 255, 255, 0.08)",
                color: "var(--text-primary)",
                border: "1px solid var(--border-color)",
                fontWeight: "600",
                fontSize: "0.85rem",
                cursor: "pointer",
              }}
            >
              <Edit3 size={15} /> Edit Output
            </button>

            <button
              onClick={handleReject}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "9px 18px",
                borderRadius: "8px",
                background: "rgba(244, 63, 94, 0.15)",
                color: "#fb7185",
                border: "1px solid #f43f5e",
                fontWeight: "600",
                fontSize: "0.85rem",
                cursor: "pointer",
              }}
            >
              <X size={15} /> Reject
            </button>
          </>
        ) : (
          <>
            <button
              onClick={handleEditSubmit}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "9px 18px",
                borderRadius: "8px",
                background: "#6366f1",
                color: "#ffffff",
                border: "none",
                fontWeight: "600",
                fontSize: "0.85rem",
                cursor: "pointer",
              }}
            >
              <Send size={15} /> Submit Edited Payload
            </button>
            <button
              onClick={() => setIsEditing(false)}
              style={{
                padding: "9px 14px",
                borderRadius: "8px",
                background: "transparent",
                color: "var(--text-muted)",
                border: "none",
                fontSize: "0.85rem",
                cursor: "pointer",
              }}
            >
              Cancel Edit
            </button>
          </>
        )}
      </div>
    </div>
  );
}
