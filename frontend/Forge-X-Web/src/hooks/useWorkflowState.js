import { useState, useCallback } from "react";
import orchestratorApi from "../services/orchestratorApi";

export function useWorkflowState(initialState = null) {
  const [workflow, setWorkflow] = useState(initialState);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchWorkflow = useCallback(async (workflowId) => {
    try {
      setLoading(true);
      const data = await orchestratorApi.getWorkflow(workflowId);
      setWorkflow(data);
      setError(null);
      return data;
    } catch (err) {
      setError(err.response?.data?.message || err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const handleLiveEvent = useCallback((event) => {
    setWorkflow((prev) => {
      if (!prev) return prev;

      const next = { ...prev };
      const { event_type, node_id, payload } = event;

      if (event_type === "node_started" && node_id) {
        next.current_node_id = node_id;
        next.nodes = next.nodes.map((n) =>
          n.id === node_id ? { ...n, status: "executing" } : n
        );
      } else if (event_type === "node_completed" && node_id) {
        next.nodes = next.nodes.map((n) =>
          n.id === node_id ? { ...n, status: "completed", output_data: payload?.output || n.output_data } : n
        );
      } else if (event_type === "node_failed" && node_id) {
        next.nodes = next.nodes.map((n) =>
          n.id === node_id ? { ...n, status: "failed", error_message: payload?.error } : n
        );
        next.status = "failed";
      } else if (event_type === "artifact_written") {
        const artRef = {
          artifact_id: payload?.artifact_id,
          name: payload?.name,
          summary: payload?.summary,
        };
        if (!next.artifacts.some((a) => a.artifact_id === artRef.artifact_id)) {
          next.artifacts = [...next.artifacts, artRef];
        }
        if (node_id) {
          next.nodes = next.nodes.map((n) =>
            n.id === node_id
              ? { ...n, artifact_refs: [...(n.artifact_refs || []), artRef.artifact_id] }
              : n
          );
        }
      } else if (event_type === "plan_updated") {
        next.plan_version = payload?.plan_version || next.plan_version + 1;
        next.replan_count = payload?.replan_count || next.replan_count + 1;
        if (payload?.nodes) {
          next.nodes = payload.nodes;
        }
      } else if (event_type === "interrupt_requested") {
        next.status = "awaiting_approval";
        next.pending_approval = payload;
        if (node_id) {
          next.nodes = next.nodes.map((n) =>
            n.id === node_id ? { ...n, status: "awaiting_approval" } : n
          );
        }
      } else if (event_type === "hitl_resolved") {
        next.pending_approval = null;
        next.status = payload?.decision === "rejected" ? "failed" : "executing";
      } else if (event_type === "workflow_completed") {
        next.status = "completed";
      } else if (event_type === "workflow_failed") {
        next.status = "failed";
      } else if (event_type === "workflow_cancelled") {
        next.status = "cancelled";
      }

      return next;
    });
  }, []);

  return {
    workflow,
    setWorkflow,
    loading,
    error,
    fetchWorkflow,
    handleLiveEvent,
  };
}
