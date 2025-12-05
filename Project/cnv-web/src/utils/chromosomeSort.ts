// Chromosome sort order for biological data
export const CHROMOSOME_ORDER: Record<string, number> = {
  "1": 1,
  "2": 2,
  "3": 3,
  "4": 4,
  "5": 5,
  "6": 6,
  "7": 7,
  "8": 8,
  "9": 9,
  "10": 10,
  "11": 11,
  "12": 12,
  "13": 13,
  "14": 14,
  "15": 15,
  "16": 16,
  "17": 17,
  "18": 18,
  "19": 19,
  "20": 20,
  "21": 21,
  "22": 22,
  X: 23,
  Y: 24,
  MT: 25,
};

// Type for data with chromosome and start fields
export type ChromosomeData = {
  chromosome: string | number;
  start: number;
  [key: string]: any;
};

// Sort data by chromosome order and start position
export function sortByChromosome<T extends ChromosomeData>(data: T[]): T[] {
  return [...data].sort((a, b) => {
    const chrA = typeof a.chromosome === "string" ? a.chromosome : String(a.chromosome);
    const chrB = typeof b.chromosome === "string" ? b.chromosome : String(b.chromosome);

    const orderA = CHROMOSOME_ORDER[chrA] ?? 999;
    const orderB = CHROMOSOME_ORDER[chrB] ?? 999;

    if (orderA !== orderB) {
      return orderA - orderB;
    }

    // If same chromosome, sort by start position
    return a.start - b.start;
  });
}
