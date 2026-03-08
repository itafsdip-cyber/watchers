'use client';

import 'maplibre-gl/dist/maplibre-gl.css';

import { useEffect, useRef } from 'react';

import { Incident } from '@/lib/types';
import { incidentsToGeoJson } from '@/lib/map';

type Props = {
  incidents: Incident[];
};

export function IncidentMap({ incidents }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let map: import('maplibre-gl').Map | undefined;

    async function initMap() {
      if (!containerRef.current) return;
      const maplibregl = await import('maplibre-gl');

      map = new maplibregl.Map({
        container: containerRef.current,
        style: 'https://demotiles.maplibre.org/style.json',
        center: [55.2962, 25.2744],
        zoom: 8
      });

      map.addControl(new maplibregl.NavigationControl(), 'top-right');

      const bounds = new maplibregl.LngLatBounds();
      const features = incidentsToGeoJson(incidents).features;

      map.on('load', () => {
        map?.addSource('incidents', {
          type: 'geojson',
          data: incidentsToGeoJson(incidents),
          cluster: true,
          clusterMaxZoom: 14,
          clusterRadius: 50
        });

        map?.addLayer({
          id: 'clusters',
          type: 'circle',
          source: 'incidents',
          filter: ['has', 'point_count'],
          paint: {
            'circle-color': '#23d3a1',
            'circle-radius': ['step', ['get', 'point_count'], 16, 15, 20, 30, 24],
            'circle-opacity': 0.85
          }
        });

        map?.addLayer({
          id: 'cluster-count',
          type: 'symbol',
          source: 'incidents',
          filter: ['has', 'point_count'],
          layout: {
            'text-field': ['get', 'point_count_abbreviated'],
            'text-size': 12
          },
          paint: { 'text-color': '#0b1115' }
        });

        map?.addLayer({
          id: 'unclustered-point',
          type: 'circle',
          source: 'incidents',
          filter: ['!', ['has', 'point_count']],
          paint: {
            'circle-radius': 7,
            'circle-color': [
              'match',
              ['get', 'status'],
              'confirmed',
              '#23d3a1',
              'officially_confirmed',
              '#23d3a1',
              'disputed',
              '#ff8f5b',
              '#a78bfa'
            ],
            'circle-stroke-width': 1,
            'circle-stroke-color': '#ffffff'
          }
        });

        map?.on('click', 'clusters', (event) => {
          const featuresAtPoint = map?.queryRenderedFeatures(event.point, { layers: ['clusters'] });
          const clusterId = featuresAtPoint?.[0]?.properties?.cluster_id;
          const source = map?.getSource('incidents') as import('maplibre-gl').GeoJSONSource;
          source.getClusterExpansionZoom(clusterId, (err, zoom) => {
            if (err || !featuresAtPoint?.[0]?.geometry || featuresAtPoint[0].geometry.type !== 'Point') return;
            map?.easeTo({ center: featuresAtPoint[0].geometry.coordinates as [number, number], zoom });
          });
        });

        map?.on('click', 'unclustered-point', (event) => {
          const feature = event.features?.[0];
          if (!feature || feature.geometry.type !== 'Point') return;
          const props = feature.properties as { title?: string; status?: string; credibility_score?: number };
          new maplibregl.Popup({ offset: 18 })
            .setLngLat(feature.geometry.coordinates as [number, number])
            .setHTML(
              `<strong>${props.title ?? ''}</strong><br/>Status: ${props.status ?? ''}<br/>Score: ${Math.round(
                Number(props.credibility_score ?? 0) * 100
              )}%`
            )
            .addTo(map as import('maplibre-gl').Map);
        });

        map?.on('mouseenter', 'clusters', () => {
          if (map) map.getCanvas().style.cursor = 'pointer';
        });
        map?.on('mouseleave', 'clusters', () => {
          if (map) map.getCanvas().style.cursor = '';
        });
      });

      features.forEach((feature) => bounds.extend(feature.geometry.coordinates));
      if (features.length > 0) {
        map.fitBounds(bounds, { padding: 48, maxZoom: 11 });
      }
    }

    void initMap();

    return () => {
      map?.remove();
    };
  }, [incidents]);

  return <div ref={containerRef} className="h-[360px] w-full rounded-2xl border border-white/10" />;
}
