import axiosClient from "../config/axiosClient";

export const orchestratorApi = {
  // Plan workflow from query
  planWorkflow: async (payload) => {
    const response = await axiosClient.post("/plan", payload);
    return response.data;
  },

  // Execute workflow (returns 202 Accepted)
  executeWorkflow: async (workflowId, payload = {}) => {
    const response = await axiosClient.post(`/${workflowId}/execute`, payload);
    return response.data;
  },

  // Fetch workflow state
  getWorkflow: async (workflowId) => {
    const response = await axiosClient.get(`/${workflowId}`);
    return response.data;
  },

  // Fetch XYFlow graph data
  getWorkflowGraph: async (workflowId) => {
    const response = await axiosClient.get(`/${workflowId}/graph`);
    return response.data;
  },

  // List recent workflows
  listWorkflows: async (limit = 20) => {
    const response = await axiosClient.get("", { params: { limit } });
    return response.data;
  },

  // Resume HITL approval
  resumeWorkflow: async (workflowId, payload) => {
    const response = await axiosClient.post(`/${workflowId}/hitl/resume`, payload);
    return response.data;
  },

  // Cancel workflow
  cancelWorkflow: async (workflowId, reason = "Cancelled by user") => {
    const response = await axiosClient.post(`/${workflowId}/cancel`, { reason });
    return response.data;
  },

  // Fetch artifact content
  getArtifact: async (workflowId, artifactId) => {
    const response = await axiosClient.get(`/${workflowId}/artifacts/${artifactId}`);
    return response.data;
  },

  // Fetch agent catalog
  getAgents: async () => {
    const response = await axiosClient.get("/agents");
    return response.data;
  },

  // Health check
  getHealth: async () => {
    const response = await axiosClient.get("/health");
    return response.data;
  },
};

export default orchestratorApi;
