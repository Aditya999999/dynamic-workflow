// Office portable environment configuration wrapper
const getEnv = (key, defaultValue = "") => {
  if (typeof import.meta !== "undefined" && import.meta.env) {
    return import.meta.env[key] || defaultValue;
  }
  if (typeof process !== "undefined" && process.env) {
    return process.env[key] || defaultValue;
  }
  return defaultValue;
};

const mode = typeof import.meta !== "undefined" && import.meta.env?.MODE ? import.meta.env.MODE : "development";

const urlDev = getEnv("VITE_ORCHESTRATOR_API_URL_DEV", "http://localhost:8000");
const urlStaging = getEnv("VITE_ORCHESTRATOR_API_URL_STAGING", "");
const urlProd = getEnv("VITE_ORCHESTRATOR_API_URL_PROD", "");

// Resolve active API URL based on build mode or fallback priority
let activeUrl = urlDev;
let currentEnv = "dev";

if (mode === "production" && urlProd) {
  activeUrl = urlProd;
  currentEnv = "prod";
} else if ((mode === "staging" || mode === "stage") && urlStaging) {
  activeUrl = urlStaging;
  currentEnv = "staging";
} else if (urlDev) {
  activeUrl = urlDev;
  currentEnv = "dev";
} else if (urlProd) {
  activeUrl = urlProd;
  currentEnv = "prod";
}

export const environment = {
  appEnvironment: currentEnv,
  orchestratorApiUrl: activeUrl,
  urlDev,
  urlStaging,
  urlProd,
};
