import { Incident } from './types';

export type IncidentGeoJson = {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    geometry: {
      type: 'Point';
      coordinates: [number, number];
    };
    properties: {
      id: number;
      title: string;
      status: string;
      credibility_score: number;
    };
  }>;
};

export function incidentsToGeoJson(incidents: Incident[]): IncidentGeoJson {
  return {
    type: 'FeatureCollection',
    features: incidents
      .filter((incident) => incident.longitude != null && incident.latitude != null)
      .map((incident) => ({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [incident.longitude as number, incident.latitude as number]
        },
        properties: {
          id: incident.id,
          title: incident.title,
          status: incident.status,
          credibility_score: incident.credibility_score
        }
      }))
  };
}
