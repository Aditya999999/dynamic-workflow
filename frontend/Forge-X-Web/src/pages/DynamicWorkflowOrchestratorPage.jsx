import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { QueryInput } from "../components/DynamicWorkflowOrchestrator/QueryInput/QueryInput";
import orchestratorApi from "../services/orchestratorApi";
import { routesPath } from "../routes/routesPath";
import { History, ArrowRight, Bot, Cpu, CheckCircle2, AlertTriangle, Clock } from "lucide-react";

export function DynamicWorkflowOrchestratorPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [recentWorkflows, setRecentWorkflows] = useState([]);

  useEffect(() => {
    orchestratorApi
      .listWorkflows(10)
      .then((data) => setRecentWorkflows(data))
      .catch((err) => console.debug("Could not fetch recent workflows:", err));
  }, []);

  const handlePlanWorkflow = async (query) => {
    try {
      setLoading(true);
      const state = await orchestratorApi.planWorkflow({ query });
      navigate(routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR_DETAIL.replace(":workflowId", state.workflow_id));
    } catch (err) {
      alert("Failed to plan workflow: " + (err.response?.data?.message || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "40px 20px" }}>
      <QueryInput onPlanWorkflow={handlePlanWorkflow} loading={loading} />

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
                        background: wf.status === "completed" ? "rgba(16, 185, 129, 0.15)" : "rgba(99, 102, 241, 0.15)",
                        color: wf.status === "completed" ? "#34d399" : "#818cf8",
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

                <ArrowRight size={16} color="var(--text-muted)" />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default DynamicWorkflowOrchestratorPage;
