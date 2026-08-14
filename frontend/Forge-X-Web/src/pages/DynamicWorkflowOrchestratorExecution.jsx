import React, { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useWorkflowState } from "../hooks/useWorkflowState";
import { useOrchestratorEvents } from "../hooks/useOrchestratorEvents";
import orchestratorApi from "../services/orchestratorApi";
import { routesPath } from "../routes/routesPath";

import { PlanSummary } from "../components/DynamicWorkflowOrchestrator/PlanSummary/PlanSummary";
import { PendingApprovals } from "../components/DynamicWorkflowOrchestrator/HITLPanel/PendingApprovals";
import { WorkflowGraph } from "../components/DynamicWorkflowOrchestrator/WorkflowGraph/WorkflowGraph";
import { ArtifactBrowser } from "../components/DynamicWorkflowOrchestrator/ArtifactViewer/ArtifactBrowser";
import { ArtifactPreview } from "../components/DynamicWorkflowOrchestrator/ArtifactViewer/ArtifactPreview";
import { AgentDetailsPanel } from "../components/DynamicWorkflowOrchestrator/AgentDetails/AgentDetailsPanel";
import { EventTimeline } from "../components/DynamicWorkflowOrchestrator/EventTimeline/EventTimeline";
import { ArrowLeft, RefreshCw } from "lucide-react";

export function DynamicWorkflowOrchestratorExecution() {
  const { workflowId } = useParams();
  const navigate = useNavigate();

  const { workflow, loading, error, fetchWorkflow, handleLiveEvent } = useWorkflowState();
  const { isConnected, events } = useOrchestratorEvents(workflowId, handleLiveEvent);

  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [previewArtifactId, setPreviewArtifactId] = useState(null);
  const [executing, setExecuting] = useState(false);
  const [graphData, setGraphData] = useState(null);

  // Initial workflow fetch
  useEffect(() => {
    if (workflowId) {
      fetchWorkflow(workflowId);
    }
  }, [workflowId, fetchWorkflow]);

  // Fetch graph data whenever workflow updates
  useEffect(() => {
    if (workflowId) {
      orchestratorApi
        .getWorkflowGraph(workflowId)
        .then((data) => setGraphData(data))
        .catch((err) => console.debug("Graph fetch notice:", err));
    }
  }, [workflowId, workflow]);

  // Selected node object
  const selectedNode = useMemo(() => {
    if (!workflow || !selectedNodeId) return null;
    return workflow.nodes.find((n) => n.id === selectedNodeId) || null;
  }, [workflow, selectedNodeId]);

  // Start execution handler
  const handleExecute = async (autoApprove = false) => {
    try {
      setExecuting(true);
      await orchestratorApi.executeWorkflow(workflowId, { auto_approve_hitl: autoApprove });
      await fetchWorkflow(workflowId);
    } catch (err) {
      alert("Failed to start execution: " + (err.response?.data?.message || err.message));
    } finally {
      setExecuting(false);
    }
  };

  // Cancel execution handler
  const handleCancel = async () => {
    try {
      await orchestratorApi.cancelWorkflow(workflowId, "Cancelled by user via UI");
      await fetchWorkflow(workflowId);
    } catch (err) {
      alert("Failed to cancel: " + (err.response?.data?.message || err.message));
    }
  };

  // Resume HITL approval handler
  const handleResolveHITL = async (resolution) => {
    try {
      await orchestratorApi.resumeWorkflow(workflowId, resolution);
      await fetchWorkflow(workflowId);
    } catch (err) {
      alert("Failed to resume approval: " + (err.response?.data?.message || err.message));
    }
  };

  if (loading && !workflow) {
    return (
      <div style={{ textAlign: "center", padding: "80px 0", color: "var(--text-muted)" }}>
        Loading workflow orchestration...
      </div>
    );
  }

  if (error && !workflow) {
    return (
      <div style={{ maxWidth: "800px", margin: "60px auto", padding: "20px" }}>
        <div style={{ color: "#fb7185", background: "rgba(244, 63, 94, 0.1)", padding: "16px", borderRadius: "10px", marginBottom: "16px" }}>
          {error}
        </div>
        <button
          onClick={() => navigate(routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR)}
          style={{
            padding: "8px 16px",
            borderRadius: "6px",
            background: "var(--bg-input)",
            color: "var(--text-primary)",
            border: "1px solid var(--border-color)",
            cursor: "pointer",
          }}
        >
          Back to Orchestrator
        </button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: "1500px", margin: "0 auto", padding: "24px 20px" }}>
      {/* Top Bar Navigation */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <button
          onClick={() => navigate(routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR)}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            padding: "6px 12px",
            borderRadius: "6px",
            background: "transparent",
            color: "var(--text-secondary)",
            border: "1px solid var(--border-color)",
            fontSize: "0.82rem",
            cursor: "pointer",
          }}
        >
          <ArrowLeft size={15} /> All Workflows
        </button>

        <button
          onClick={() => fetchWorkflow(workflowId)}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            padding: "6px 12px",
            borderRadius: "6px",
            background: "var(--bg-input)",
            color: "var(--text-secondary)",
            border: "1px solid var(--border-color)",
            fontSize: "0.82rem",
            cursor: "pointer",
          }}
        >
          <RefreshCw size={13} /> Refresh State
        </button>
      </div>

      {/* Plan Summary Header */}
      <PlanSummary
        workflow={workflow}
        onExecute={handleExecute}
        onCancel={handleCancel}
        executing={executing}
      />

      {/* Pending HITL Approvals Alert Card */}
      <PendingApprovals
        pendingApproval={workflow?.pending_approval}
        onResolve={handleResolveHITL}
        onPreviewArtifact={(artId) => setPreviewArtifactId(artId)}
      />

      {/* Main Execution Workspace: Graph & Split Panels */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: "20px" }}>
        {/* Left Column: Interactive Graph & Artifact Gallery */}
        <div>
          <WorkflowGraph
            graphData={graphData}
            onSelectNode={(nodeId) => setSelectedNodeId(nodeId)}
          />

          {selectedNode && (
            <AgentDetailsPanel
              node={selectedNode}
              onClose={() => setSelectedNodeId(null)}
              onPreviewArtifact={(artId) => setPreviewArtifactId(artId)}
            />
          )}

          <ArtifactBrowser
            artifacts={workflow?.artifacts || []}
            onSelectArtifact={(artId) => setPreviewArtifactId(artId)}
          />
        </div>

        {/* Right Column: Live Event Stream Feed */}
        <div>
          <EventTimeline events={events} isConnected={isConnected} />
        </div>
      </div>

      {/* Artifact Preview Slide-over Drawer */}
      {previewArtifactId && (
        <ArtifactPreview
          workflowId={workflowId}
          artifactId={previewArtifactId}
          onClose={() => setPreviewArtifactId(null)}
        />
      )}
    </div>
  );
}

export default DynamicWorkflowOrchestratorExecution;
