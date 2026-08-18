import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { QueryInput } from "../components/DynamicWorkflowOrchestrator/QueryInput/QueryInput";
import orchestratorApi from "../services/orchestratorApi";
import { routesPath } from "../routes/routesPath";
import { History, ArrowRight, Trash2 } from "lucide-react";

export function DynamicWorkflowOrchestratorPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [recentWorkflows, setRecentWorkflows] = useState([]);
  const [deletingId, setDeletingId] = useState(null);

  const fetchWorkflows = () => {
    orchestratorApi
      .listWorkflows(10)
      .then((data) => setRecentWorkflows(data))
      .catch((err) => console.debug("Could not fetch recent workflows:", err));
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const handlePlanWorkflow = async (query) => {
    try {
      setLoading(true);
      setErrorMessage(null);
      const state = await orchestratorApi.planWorkflow({ query });

      if (state.status === "failed" && (!state.nodes || state.nodes.length === 0)) {
        setErrorMessage(
          state.error_message ||
          "Your request appears to be outside the scope of Software Development Life Cycle (SDLC) workflows. " +
          "The Dynamic Workflow Orchestrator handles tasks such as Requirements Analysis (BRD), Architecture Design, " +
          "Sprint Planning, Microservice Development, and QA/Test Strategy. Please provide a software engineering requirement."
        );
        return;
      }

      navigate(routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR_DETAIL.replace(":workflowId", state.workflow_id));
    } catch (err) {
      const detailMsg = err.response?.data?.detail || err.response?.data?.message || err.message;
      setErrorMessage(detailMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteWorkflow = async (e, workflowId) => {
    e.stopPropagation();
    try {
      setDeletingId(workflowId);
      // Optimistically remove from state
      setRecentWorkflows((prev) => prev.filter((wf) => wf.workflow_id !== workflowId));
      await orchestratorApi.deleteWorkflow(workflowId);
    } catch (err) {
      console.error("Failed to delete workflow:", err);
      // Re-fetch in case of failure
      fetchWorkflows();
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "40px 20px" }}>
      <QueryInput
        onPlanWorkflow={handlePlanWorkflow}
        loading={loading}
        errorMessage={errorMessage}
        onClearError={() => setErrorMessage(null)}
      />

      {/* Recent Workflows */}
      {recentWorkflows.length > 0 && (
        <div style={{ marginTop: "40px", maxWidth: "900px", margin: "40px auto 0" }}>
          <h3 style={{ fontSize: "1.1rem", fontWeight: "700", marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
            <History size={18} color="var(--primary)" /> Recent Orchestrations
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {recentWorkflows.map((wf) => (
              <div
                key={wf.workflow_id}
                onClick={() => navigate(routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR_DETAIL.replace(":workflowId", wf.workflow_id))}
                className="glass-panel glow-hover"
                style={{
                  padding: "16px 20px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  opacity: deletingId === wf.workflow_id ? 0.4 : 1,
                }}
              >
                <div style={{ flex: 1, marginRight: "16px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {wf.workflow_id}
                    </span>
                    <span
                      style={{
                        fontSize: "0.72rem",
                        padding: "2px 8px",
                        borderRadius: "12px",
                        background:
                          wf.status === "completed"
                            ? "rgba(16, 185, 129, 0.15)"
                            : wf.status === "failed"
                            ? "rgba(239, 68, 68, 0.15)"
                            : "rgba(99, 102, 241, 0.15)",
                        color:
                          wf.status === "completed"
                            ? "#34d399"
                            : wf.status === "failed"
                            ? "#f87171"
                            : "#818cf8",
                        fontWeight: "600",
                        textTransform: "capitalize",
                      }}
                    >
                      {wf.status}
                    </span>
                    <span style={{ fontSize: "0.72rem", color: "#c084fc" }}>
                      Plan v{wf.plan_version}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.9rem", fontWeight: "600", color: "var(--text-primary)" }}>
                    {wf.query}
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <button
                    type="button"
                    onClick={(e) => handleDeleteWorkflow(e, wf.workflow_id)}
                    title="Delete workflow"
                    style={{
                      background: "rgba(255, 255, 255, 0.04)",
                      border: "1px solid rgba(255, 255, 255, 0.08)",
                      borderRadius: "8px",
                      padding: "8px",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "var(--text-muted)",
                      transition: "all 0.15s ease",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "rgba(239, 68, 68, 0.15)";
                      e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.4)";
                      e.currentTarget.style.color = "#ef4444";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "rgba(255, 255, 255, 0.04)";
                      e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
                      e.currentTarget.style.color = "var(--text-muted)";
                    }}
                  >
                    <Trash2 size={16} />
                  </button>

                  <ArrowRight size={16} color="var(--text-muted)" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default DynamicWorkflowOrchestratorPage;
