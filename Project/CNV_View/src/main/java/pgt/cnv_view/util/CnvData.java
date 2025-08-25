package pgt.cnv_view.util;

import java.nio.file.*;
import java.util.List;

/**
 * Central utilities & constants for CNV data handling to avoid logic duplication
 * across multiple controllers.
 */
public final class CnvData {

    private CnvData() {}

    // Supported algorithms (normalized tokens)
    public static final List<String> ALGORITHMS = List.of("baseline", "bicseq2", "wisecondorx", "bluefuse");

    // Human readable pretty names (subset only where formatting differs)
    public static String prettyAlgorithm(String token) {
        if (token == null) return "";
        return switch (token.toLowerCase()) {
            case "bicseq2" -> "BIC-seq2";
            case "wisecondorx" -> "WISECONDORX";
            case "bluefuse" -> "BlueFuse";
            case "baseline" -> "Baseline";
            default -> token;
        };
    }

    // Standard chromosome ordering
    public static final List<String> CHROMOSOMES = List.of(
            "1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","X","Y"
    );

    // Normalize algorithm text from UI (remove spaces, lowercase, map bic variations)
    public static String normalizeAlgorithm(String displayText) {
        if (displayText == null) return null;
        String t = displayText.toLowerCase().replaceAll("\\s+", "");
        if (t.contains("bic")) return "bicseq2"; // unify any BIC variations
        return t;
    }

    // File name helpers
    public static String binsFileName(String sample, String algoToken) {
        return sample + '_' + algoToken + "_bins.tsv";
    }
    public static String segmentsFileName(String sample, String algoToken) {
        return sample + '_' + algoToken + "_segments.tsv";
    }

    // Resolve data root inside resources if present (preferred), else external ./data
    public static Path resolveDataRoot() {
        Path projectData = Paths.get("src", "main", "resources", "pgt", "cnv_view", "Data");
        if (Files.exists(projectData)) return projectData;
        return Paths.get(System.getProperty("user.dir"), "data");
    }

    // Writable version (used when adding new samples). Mirrors AddSampleController logic.
    public static Path resolveWritableDataRoot() throws java.io.IOException {
        Path projectData = Paths.get("src", "main", "resources", "pgt", "cnv_view", "Data");
        if (Files.exists(projectData) && Files.isDirectory(projectData) && Files.isWritable(projectData)) {
            return projectData;
        }
        Path external = Paths.get(System.getProperty("user.dir"), "data");
        Files.createDirectories(external);
        return external;
    }

    // Check if a sample has the algorithm (both bins & segments files exist)
    public static boolean sampleHasAlgorithm(String sampleName, String algoToken) {
        try {
            Path dir = resolveDataRoot().resolve(sampleName).resolve(algoToken);
            if (!Files.isDirectory(dir)) return false;
            return Files.exists(dir.resolve(binsFileName(sampleName, algoToken))) &&
                    Files.exists(dir.resolve(segmentsFileName(sampleName, algoToken)));
        } catch (Exception e) {
            return false;
        }
    }

    // Any algorithm present under sample directory?
    public static boolean sampleDirectoryHasAnyAlgorithm(String sampleName) {
        for (String algo : ALGORITHMS) {
            if (sampleHasAlgorithm(sampleName, algo)) return true;
        }
        return false;
    }

    // -------- Sample name parsing --------
    // Format: FlowcellID-CycleID-EmbryoID where FlowcellID & EmbryoID contain no '-', CycleID may contain '-'
    public record SampleParts(String flowcell, String cycle, String embryo) {}

    public static SampleParts parseSample(String sample) {
        if (sample == null || sample.isBlank()) return new SampleParts(sample, sample, sample);
        String[] tokens = sample.split("-");
        if (tokens.length < 3) { // fallback: cannot reliably split
            return new SampleParts(sample, sample, sample);
        }
        String flowcell = tokens[0];
        String embryo = tokens[tokens.length - 1];
        StringBuilder cycle = new StringBuilder();
        for (int i = 1; i < tokens.length - 1; i++) {
            if (i > 1) cycle.append('-');
            cycle.append(tokens[i]);
        }
        return new SampleParts(flowcell, cycle.toString(), embryo);
    }

    public static String cycleId(String sample) { return parseSample(sample).cycle(); }
    public static String flowcellId(String sample) { return parseSample(sample).flowcell(); }
    public static String embryoId(String sample) { return parseSample(sample).embryo(); }
    // Display name used in chart/report titles: FlowcellID-EmbryoID
    public static String displaySampleName(String sample) {
        SampleParts p = parseSample(sample);
        return p.flowcell() + '-' + p.embryo();
    }
}
