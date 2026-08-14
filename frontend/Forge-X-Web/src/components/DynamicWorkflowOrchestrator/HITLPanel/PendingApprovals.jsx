import React from "react";
import { ApprovalCard } from "./ApprovalCard";

export function PendingApprovals({ pendingApproval, onResolve, onPreviewArtifact }) {
  if (!pendingApproval) return null;

  return (
    <div style={{ marginBottom: "20px" }}>
      <ApprovalCard
        pendingApproval={pendingApproval}
        onResolve={onResolve}
        onPreviewArtifact={onPreviewArtifact}
      />
    </div>
  );
}
