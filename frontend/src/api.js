const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

function json(body) {
  return { headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

export const api = {
  getTaxonomy: () => request("/api/taxonomy"),

  login: (mobileNumber, carNumber) =>
    request("/api/auth/login", { method: "POST", ...json({ mobile_number: mobileNumber, car_number: carNumber }) }),

  updateCar: (carNumber, details) =>
    request(`/api/cars/${encodeURIComponent(carNumber)}`, { method: "PUT", ...json(details) }),

  createReport: (carNumber) =>
    request("/api/reports", { method: "POST", ...json({ car_number: carNumber }) }),

  addReportItem: (reportId, part, file) => {
    const formData = new FormData();
    formData.append("part", part);
    formData.append("file", file);
    return request(`/api/reports/${reportId}/items`, { method: "POST", body: formData });
  },

  getReport: (reportId) => request(`/api/reports/${reportId}`),
};
