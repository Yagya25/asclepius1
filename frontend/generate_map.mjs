import fs from "fs";
import * as turf from "@turf/turf";

const stateToZone = {
  "Haryana": "North", "Himachal Pradesh": "North", "Jammu and Kashmir": "North",
  "Punjab": "North", "Rajasthan": "North", "Chandigarh": "North", "NCT of Delhi": "North", "Delhi": "North",

  "Andhra Pradesh": "South", "Karnataka": "South", "Kerala": "South",
  "Tamil Nadu": "South", "Telangana": "South", "Puducherry": "South",

  "Bihar": "East", "Jharkhand": "East", "Odisha": "East", "West Bengal": "East",

  "Goa": "West", "Gujarat": "West", "Maharashtra": "West",
  "Dadra and Nagar Haveli": "West", "Daman and Diu": "West", "Dadra and Nagar Haveli and Daman and Diu": "West",

  "Chhattisgarh": "Central", "Madhya Pradesh": "Central", "Uttar Pradesh": "Central",
  "Uttarakhand": "Central",

  "Arunachal Pradesh": "Northeast", "Assam": "Northeast", "Manipur": "Northeast",
  "Meghalaya": "Northeast", "Mizoram": "Northeast", "Nagaland": "Northeast",
  "Sikkim": "Northeast", "Tripura": "Northeast",
};

async function main() {
  console.log("Fetching GeoJSON...");
  const res = await fetch(
    "https://raw.githubusercontent.com/geohacker/india/master/state/india_state.geojson"
  );
  const raw = await res.json();
  console.log(`Fetched ${raw.features.length} state features.`);

  // Tag zone + flatten MultiPolygons
  const tagged = turf.flatten(raw);
  tagged.features.forEach((f) => {
    const name = f.properties?.NAME_1 ?? f.properties?.name;
    f.properties.zone = stateToZone[name] ?? "Unknown";
  });

  const dissolved = turf.dissolve(tagged, { propertyName: "zone" });

  dissolved.features.forEach((f, i) => {
    if (!f.properties?.zone) {
      const centroid = turf.centroid(f);
      const match = tagged.features.find((t) =>
        turf.booleanPointInPolygon(centroid, t)
      );
      f.properties = { zone: match?.properties?.zone ?? "Unknown" };
    }
  });

  const targetPath = "./public/india-zones.geojson";
  fs.writeFileSync(
    targetPath,
    JSON.stringify(dissolved)
  );
  console.log(`Wrote ${dissolved.features.length} zone shapes to ${targetPath}`);
}

main().catch(err => {
  console.error("Error generating map:", err);
  process.exit(1);
});
