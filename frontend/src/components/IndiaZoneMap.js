import React, { useEffect, useState, useMemo } from "react";
import { geoMercator, geoPath } from "d3-geo";
import { inr } from "@/lib/api";

const defaultZoneStats = {
  North: { profit: 42000000, percent: 30 },
  South: { profit: 35000000, percent: 25 },
  East: { profit: 24500000, percent: 17 },
  West: { profit: 38000000, percent: 27 },
  Central: { profit: 14000000, percent: 10 },
  Northeast: { profit: 6000000, percent: 4 },
};

export default function IndiaZoneMap({ regions = [] }) {
  const [geojson, setGeojson] = useState(null);
  const [hoveredZone, setHoveredZone] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    fetch("/india-zones.geojson")
      .then((res) => res.json())
      .then((data) => setGeojson(data))
      .catch((err) => console.error("Error loading india-zones.geojson:", err));
  }, []);

  const zoneData = useMemo(() => {
    if (!regions || regions.length === 0) return defaultZoneStats;
    const map = {};
    let total = 0;
    regions.forEach((r) => {
      const val = r.revenue || r.profit || r.value || 0;
      total += val;
      map[r.name] = { profit: val, percent: 0 };
    });
    if (total > 0) {
      Object.keys(map).forEach((k) => {
        map[k].percent = Math.round((map[k].profit / total) * 100);
      });
    }
    return { ...defaultZoneStats, ...map };
  }, [regions]);

  const { paths, width, height } = useMemo(() => {
    const w = 420;
    const h = 420;
    if (!geojson) return { paths: [], width: w, height: h };

    const projection = geoMercator().fitExtent(
      [[20, 20], [w - 20, h - 20]],
      geojson
    );
    const pathGenerator = geoPath().projection(projection);

    const featurePaths = geojson.features.map((feature, i) => {
      const zoneName = feature.properties?.zone || "Unknown";
      const d = pathGenerator(feature);
      return {
        id: i,
        zone: zoneName,
        d,
      };
    });

    return { paths: featurePaths, width: w, height: h };
  }, [geojson]);

  function getColor(zone) {
    const percent = zoneData[zone]?.percent ?? 0;
    if (percent >= 30) return "hsl(243 75% 50%)";
    if (percent >= 20) return "hsl(243 70% 62%)";
    if (percent >= 10) return "hsl(243 65% 74%)";
    if (percent > 0) return "hsl(243 60% 84%)";
    return "hsl(220 14% 90%)";
  }

  if (!geojson) {
    return (
      <div className="flex h-64 items-center justify-center text-xs text-muted-foreground animate-pulse">
        Loading India Zone Map…
      </div>
    );
  }

  return (
    <div className="relative w-full flex flex-col items-center">
      <div className="relative w-full max-w-[420px] aspect-[4/4.2]">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-full drop-shadow-sm select-none"
        >
          <g>
            {paths.map((p) => {
              const isHovered = hoveredZone === p.zone;
              return (
                <path
                  key={p.id}
                  d={p.d}
                  fill={getColor(p.zone)}
                  stroke="hsl(0 0% 100%)"
                  strokeWidth={isHovered ? 2 : 1}
                  className="transition-all duration-200 cursor-pointer hover:opacity-90"
                  onMouseEnter={(e) => {
                    setHoveredZone(p.zone);
                  }}
                  onMouseMove={(e) => {
                    const rect = e.currentTarget.ownerSVGElement.getBoundingClientRect();
                    setTooltipPos({
                      x: e.clientX - rect.left,
                      y: e.clientY - rect.top,
                    });
                  }}
                  onMouseLeave={() => setHoveredZone(null)}
                />
              );
            })}
          </g>
        </svg>

        {/* Hover Tooltip */}
        {hoveredZone && (
          <div
            className="pointer-events-none absolute z-20 rounded-lg border border-border bg-popover/95 backdrop-blur px-3 py-2 shadow-xl -translate-x-1/2 -translate-y-full mb-2"
            style={{ left: `${tooltipPos.x}px`, top: `${tooltipPos.y}px` }}
          >
            <p className="mono text-[11px] font-semibold text-foreground">
              {hoveredZone} Zone
            </p>
            <div className="flex items-center gap-3 mt-1 text-[11px]">
              <span className="text-muted-foreground">Revenue:</span>
              <span className="mono font-semibold text-indigo-600">
                {inr(zoneData[hoveredZone]?.profit ?? 0)}
              </span>
              <span className="mono text-[10px] text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded font-medium">
                {zoneData[hoveredZone]?.percent ?? 0}%
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Zone Legend */}
      <div className="mt-4 grid grid-cols-3 gap-2 w-full pt-3 border-t border-border/60">
        {["North", "South", "East", "West", "Central", "Northeast"].map((z) => (
          <div key={z} className="flex items-center justify-between rounded-lg bg-secondary/50 px-2.5 py-1.5 text-[11px]">
            <div className="flex items-center gap-1.5">
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: getColor(z) }}
              />
              <span className="font-medium text-foreground">{z}</span>
            </div>
            <span className="mono text-[10px] text-muted-foreground font-semibold">
              {zoneData[z]?.percent ?? 0}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
