import { CredibilityExplanation, Incident, IncidentDetail } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

async function apiFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: 'no-store',
    headers: { Accept: 'application/json' }
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${path}`);
  }

  return (await response.json()) as T;
}

export async function getIncidents(): Promise<Incident[]> {
  return apiFetch<Incident[]>('/incidents');
}

export async function getIncident(id: number): Promise<IncidentDetail> {
  return apiFetch<IncidentDetail>(`/incidents/${id}`);
}

export async function getCredibility(id: number): Promise<CredibilityExplanation> {
  return apiFetch<CredibilityExplanation>(`/incidents/${id}/credibility`);
}
