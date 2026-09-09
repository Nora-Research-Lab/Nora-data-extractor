import { useEffect, useRef } from "react";
import maplibregl, { Map as MLMap } from "maplibre-gl";

interface Props {
  aoiGeojson: any | null;
  drawEnabled: boolean;
  onRectangleDrawn: (bbox: { north: number; south: number; east: number; west: number }) => void;
}

// Free demo raster basemap (OpenStreetMap). Swap for a production tile provider
// (MapTiler, Stadia, etc.) before going live - see docs/deployment.md.
const STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "&copy; OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
};

export default function MapPreview({ aoiGeojson, drawEnabled, onRectangleDrawn }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MLMap | null>(null);
  const drawState = useRef<{ start: [number, number] | null }>({ start: null });

  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE,
      center: [3.85, 7.95],
      zoom: 8,
    });
    mapRef.current = map;

    map.on("load", () => {
      map.addSource("aoi", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({
        id: "aoi-fill",
        type: "fill",
        source: "aoi",
        paint: { "fill-color": "#0d5c4a", "fill-opacity": 0.15 },
      });
      map.addLayer({
        id: "aoi-line",
        type: "line",
        source: "aoi",
        paint: { "line-color": "#0d5c4a", "line-width": 2 },
      });
    });

    return () => map.remove();
  }, []);

  // Update AOI layer whenever geometry changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = () => {
      const src = map.getSource("aoi") as maplibregl.GeoJSONSource | undefined;
      if (!src) return;
      src.setData(
        aoiGeojson
          ? { type: "FeatureCollection", features: [{ type: "Feature", properties: {}, geometry: aoiGeojson }] }
          : { type: "FeatureCollection", features: [] }
      );
      if (aoiGeojson) {
        const coords: [number, number][] =
          aoiGeojson.type === "Polygon" ? aoiGeojson.coordinates[0] : [];
        if (coords.length) {
          const bounds = coords.reduce(
            (b, c) => b.extend(c as [number, number]),
            new maplibregl.LngLatBounds(coords[0], coords[0])
          );
          map.fitBounds(bounds, { padding: 40, maxZoom: 12, duration: 500 });
        }
      }
    };
    if (map.isStyleLoaded()) apply();
    else map.once("load", apply);
  }, [aoiGeojson]);

  // Drag-to-draw rectangle
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const onDown = (e: maplibregl.MapMouseEvent) => {
      if (!drawEnabled) return;
      drawState.current.start = [e.lngLat.lng, e.lngLat.lat];
      map.dragPan.disable();
    };
    const onMove = (e: maplibregl.MapMouseEvent) => {
      if (!drawEnabled || !drawState.current.start) return;
      const [x0, y0] = drawState.current.start;
      const x1 = e.lngLat.lng;
      const y1 = e.lngLat.lat;
      const src = map.getSource("aoi") as maplibregl.GeoJSONSource | undefined;
      src?.setData({
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: {},
            geometry: {
              type: "Polygon",
              coordinates: [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]],
            },
          },
        ],
      });
    };
    const onUp = (e: maplibregl.MapMouseEvent) => {
      if (!drawEnabled || !drawState.current.start) return;
      const [x0, y0] = drawState.current.start;
      const x1 = e.lngLat.lng;
      const y1 = e.lngLat.lat;
      drawState.current.start = null;
      map.dragPan.enable();
      onRectangleDrawn({
        north: Math.max(y0, y1),
        south: Math.min(y0, y1),
        east: Math.max(x0, x1),
        west: Math.min(x0, x1),
      });
    };

    map.on("mousedown", onDown);
    map.on("mousemove", onMove);
    map.on("mouseup", onUp);
    return () => {
      map.off("mousedown", onDown);
      map.off("mousemove", onMove);
      map.off("mouseup", onUp);
    };
  }, [drawEnabled, onRectangleDrawn]);

  return <div className="map-box" ref={containerRef} style={{ cursor: drawEnabled ? "crosshair" : "grab" }} />;
}
