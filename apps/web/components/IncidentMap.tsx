'use client';

import 'maplibre-gl/dist/maplibre-gl.css';

import { useEffect, useRef } from 'react';

import { Incident } from '@/lib/types';

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
      let markerCount = 0;

      incidents.forEach((incident) => {
        if (incident.longitude == null || incident.latitude == null) return;
        markerCount += 1;
        bounds.extend([incident.longitude, incident.latitude]);

        const popup = new maplibregl.Popup({ offset: 18 }).setHTML(
          `<strong>${incident.title}</strong><br/>Status: ${incident.status}<br/>Score: ${Math.round(
            incident.credibility_score * 100
          )}%`
        );

        new maplibregl.Marker({ color: '#23d3a1' })
          .setLngLat([incident.longitude, incident.latitude])
          .setPopup(popup)
          .addTo(map as import('maplibre-gl').Map);
      });

      if (markerCount > 0) {
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
