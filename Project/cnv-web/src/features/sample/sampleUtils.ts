/**
 * Sample utility functions - shared across components
 */

export function parseSampleNameToParts(rawName?: string) {
  if (!rawName || rawName.trim() === "") {
    return {
      flowcell: "UNKNOWN",
      cycle: "UNKNOWN",
      embryo: rawName ?? "UNKNOWN",
      displayName: rawName ?? "UNKNOWN",
    };
  }
  const name = rawName.endsWith(".bam") ? rawName.slice(0, -4) : rawName;
  const parts = name.split("-");
  if (parts.length === 1) {
    const embryoWithPlate = parts[0];
    const embryo = embryoWithPlate.split("_")[0];
    return {
      flowcell: "UNKNOWN",
      cycle: "UNKNOWN",
      embryo,
      displayName: embryo,
    };
  }
  const flowcell = parts[0] || "UNKNOWN";
  const embryoWithPlate = parts[parts.length - 1] || "UNKNOWN";
  const embryo = embryoWithPlate.split("_")[0] || embryoWithPlate;
  const cycleParts = parts.slice(1, parts.length - 1);
  const cycle = cycleParts.join("-") || "UNKNOWN";
  return {
    flowcell,
    cycle,
    embryo,
    displayName: embryo,
  };
}
