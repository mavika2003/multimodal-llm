export type IncidentRow = Record<string, string>;

export type InspectorResult = {
  answer: string;
  citations: string[];
  abstained: boolean;
};

export type AnalyticsSummary = {
  actions_scanned: number;
  review_required: number;
  prevented: number;
  by_modality: Record<string, number>;
};

export type HealthInfo = {
  status: string;
  ollama_reachable: boolean;
  ollama_models: string[];
  offline_ready: boolean;
};