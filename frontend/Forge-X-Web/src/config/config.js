import { environment } from "./environment";

export function getOrchestratorApiBaseUrl() {
  const base = (environment.orchestratorApiUrl || "http://localhost:8000").replace(/\/$/, "");
  const prefix = "/api/dynamic-workflow";
  return `${base}${prefix}`;
}

export function getDefaultWorkspaceId() {
  return "default_workspace";
}
