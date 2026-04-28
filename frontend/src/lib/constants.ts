export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const API_ENDPOINTS = {
  PROFILE: `${API_URL}/api/profiler/profile`,
  INSIGHT: `${API_URL}/api/profiler/insight`,
  INSIGHT_STREAM: `${API_URL}/api/profiler/insight/stream`,
  HEALTH: `${API_URL}/health`,
} as const;

export const ROUTES = {
  HOME: "/",
  PROFILER: "/profiler",
  EVALUATOR: "/evaluator",
  DRIFT: "/drift",
  COST: "/cost",
} as const;

export const NAV_ITEMS = [
  { label: "Profiler", href: ROUTES.PROFILER, icon: "BarChart3" },
  { label: "Evaluator", href: ROUTES.EVALUATOR, icon: "Brain" },
  { label: "Drift", href: ROUTES.DRIFT, icon: "Activity" },
  { label: "Cost", href: ROUTES.COST, icon: "DollarSign" },
] as const;

export const MAX_UPLOAD_SIZE_MB = 50;
export const ACCEPTED_FILE_TYPES = {
  "text/csv": [".csv"],
};