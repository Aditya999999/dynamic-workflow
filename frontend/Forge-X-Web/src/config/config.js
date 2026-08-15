import { environment } from "./environment";

export function getOrchestratorApiBaseUrl() {
  const rawUrl = (environment.orchestratorApiUrl || "http://localhost:8000").trim().replace(/\/+$/, "");
  
  // If the user already provides the full path in .env (e.g. http://localhost:8000/api/dynamic-workflow)
  if (rawUrl.endsWith("/api/dynamic-workflow")) {
    return rawUrl;
  }
  
  // If only the host/domain was provided (e.g. http://localhost:8000)
  return `${rawUrl}/api/dynamic-workflow`;
}

export function getDefaultWorkspaceId() {
  return "default_workspace";
}
