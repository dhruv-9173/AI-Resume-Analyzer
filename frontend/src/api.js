import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const analyseResume = async (resumeFile, jobDescription) => {
  const formData = new FormData();
  formData.append("resume", resumeFile);
  if (jobDescription) {
    formData.append("job_description", jobDescription);
  }

  const response = await axios.post(`${BASE_URL}/api/analyse`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 120000, // 2 min timeout for AI processing
  });

  return response.data;
};

export const checkHealth = async () => {
  const response = await axios.get(`${BASE_URL}/api/health`, { timeout: 5000 });
  return response.data;
};
