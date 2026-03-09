export type Incident = {
  id: number;
  title: string;
  summary: string;
  status: string;
  credibility_score: number;
  latitude: number | null;
  longitude: number | null;
  occurred_at: string | null;
  updated_at: string;
};

export type IncidentSource = {
  id: number;
  source_name: string;
  source_url: string | null;
  source_type: string;
  reliability_score: number;
  captured_at: string;
};

export type IncidentTimelineEntry = {
  id: number;
  event_type: string;
  description: string;
  timestamp: string;
};

export type IncidentDetail = Incident & {
  sources: IncidentSource[];
  timeline_entries: IncidentTimelineEntry[];
};

export type CredibilityExplanation = {
  incident_id: number;
  final_score: number;
  dimensions: Record<string, number>;
  notes: string[];
};


export type IngestionStats = {
  total_incidents: number;
  incidents_created_today: number;
  duplicate_claims_merged_today: number;
  latest_ingest_run_timestamp: string | null;
};
