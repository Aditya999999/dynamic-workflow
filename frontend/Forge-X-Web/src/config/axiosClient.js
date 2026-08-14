import axios from "axios";
import { getOrchestratorApiBaseUrl } from "./config";

const axiosClient = axios.create({
  baseURL: getOrchestratorApiBaseUrl(),
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor
axiosClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("auth_token") || localStorage.getItem("jwt_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor
axiosClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn("Session expired or unauthorized request.");
    }
    return Promise.reject(error);
  }
);

export default axiosClient;
