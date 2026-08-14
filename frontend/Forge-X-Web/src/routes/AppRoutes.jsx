import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { routesPath } from "./routesPath";
import DynamicWorkflowOrchestratorPage from "../pages/DynamicWorkflowOrchestratorPage";
import DynamicWorkflowOrchestratorExecution from "../pages/DynamicWorkflowOrchestratorExecution";

export function AppRoutes() {
  return (
    <Routes>
      <Route
        path={routesPath.HOME}
        element={<Navigate to={routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR} replace />}
      />
      <Route
        path={routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR}
        element={<DynamicWorkflowOrchestratorPage />}
      />
      <Route
        path={routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR_DETAIL}
        element={<DynamicWorkflowOrchestratorExecution />}
      />
      <Route
        path="*"
        element={<Navigate to={routesPath.DYNAMIC_WORKFLOW_ORCHESTRATOR} replace />}
      />
    </Routes>
  );
}

export default AppRoutes;
