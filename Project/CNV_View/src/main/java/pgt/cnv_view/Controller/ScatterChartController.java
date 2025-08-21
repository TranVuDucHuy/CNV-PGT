package pgt.cnv_view.Controller;

import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.chart.NumberAxis;
import javafx.scene.chart.XYChart;
import javafx.scene.control.MenuButton;
import javafx.scene.control.Alert;
import java.nio.file.*;
import java.io.IOException;
import java.util.*;
import java.util.stream.Stream;
import javafx.application.Platform;

import java.net.URL;
import java.util.ResourceBundle;

public class ScatterChartController implements Initializable {

	@FXML
	private MenuButton chromosomeMenu; // not used now
	@FXML
	private javafx.scene.chart.ScatterChart<Number, Number> chart;

	// Showing all chromosomes simultaneously; removed single-chromosome state

	@Override
	public void initialize(URL location, ResourceBundle resources) {
		// Set default label
		if (chromosomeMenu != null) chromosomeMenu.setText("All Chromosomes");
		loadAndPlot();
	}

	@FXML
	private void onDataSelect(ActionEvent event) {
		// Data type menu removed in combined view
	}

	@FXML
	private void onChromosomeSelect(ActionEvent event) {
		// No-op now; kept to avoid FXML warnings if menu items still wired
	}

	private void loadAndPlot() {
		if (chart == null) return;
		chart.getData().clear();
		ViewController vc = ViewControllerStaticRef.get();
		if (vc == null) return;
		var samples = vc.getSelectedSampleNames();
		String algo = vc.getPrimaryAlgorithmToken();
		if (samples == null || samples.isEmpty() || algo == null) return;
		String sample = samples.get(0);
		Path binsFile = resolveDataRoot()
				.resolve(sample)
				.resolve(algo)
				.resolve(sample + "_" + algo + "_bins.tsv");
		if (!Files.exists(binsFile)) return;

		List<String> chromList = Arrays.asList("1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","X","Y");
		Map<String, List<long[]>> points = new HashMap<>(); // long[]{start, copyBits}
		Map<String, Long> chromMax = new HashMap<>(); // use max END (col2) else start

		try (Stream<String> lines = Files.lines(binsFile)) {
			lines.skip(1).filter(l -> !l.isBlank()).forEach(line -> {
				String[] p = line.split("\t");
				if (p.length < 4) return;
				String chrRaw = p[0];
				String chr = chrRaw.replaceFirst("^(?i)chr", "");
				if (!chromList.contains(chr)) return;
				String copyStr = p[3];
				if (copyStr.equalsIgnoreCase("nan")) return;
				try {
					long start = Long.parseLong(p[1]);
					long end = p.length > 2 ? parseLongSafe(p[2], start) : start;
					double copy = Double.parseDouble(copyStr);
					points.computeIfAbsent(chr, k -> new ArrayList<>()).add(new long[]{start, Double.doubleToRawLongBits(copy)});
					chromMax.merge(chr, end, Math::max);
				} catch (NumberFormatException ignored) {}
			});
		} catch (IOException e) {
			new Alert(Alert.AlertType.ERROR, "Cannot load chart data: " + e.getMessage()).showAndWait();
			return;
		}

		// Total length (sum of chrom lengths with data)
		long totalLen = chromMax.values().stream().mapToLong(Long::longValue).sum();
		if (totalLen <= 0) return;

		XYChart.Series<Number, Number> series = new XYChart.Series<>();
		series.setName(sample + " (All chr)");

		// Build cumulative offsets proportional to length; normalize to 0..totalLen
		long cumulative = 0;
		Map<String, Long> chromOffset = new HashMap<>();
		for (String chr : chromList) {
			Long len = chromMax.get(chr);
			if (len == null) continue;
			chromOffset.put(chr, cumulative);
			List<long[]> lst = points.get(chr);
			if (lst != null) {
				for (long[] arr : lst) {
					long start = arr[0];
					double copy = Double.longBitsToDouble(arr[1]);
					double x = cumulative + (double) start; // concatenated raw coordinate
					series.getData().add(new XYChart.Data<>(x, copy));
				}
			}
			cumulative += len;
		}
		chart.getData().add(series);

		// Configure axis: 0..totalLen with hidden numeric labels
		if (chart.getXAxis() instanceof NumberAxis xAxis) {
			xAxis.setAutoRanging(false);
			xAxis.setLowerBound(0);
			xAxis.setUpperBound(totalLen);
			xAxis.setTickLabelsVisible(false);
			xAxis.setMinorTickVisible(false);
			xAxis.setTickMarkVisible(false);
		}

		// Style nodes uniformly small green circles after nodes are created
		Platform.runLater(() -> {
			for (XYChart.Data<Number, Number> d : series.getData()) {
				if (d.getNode() != null) {
					d.getNode().setStyle("-fx-background-color: #038003, #038003; -fx-background-radius: 1px; -fx-padding: 1px;");
				}
			}
		});
	}

	private long parseLongSafe(String s, long fallback) {
		try { return Long.parseLong(s); } catch (NumberFormatException e) { return fallback; }
	}

	private Path resolveDataRoot() {
		Path projectData = Paths.get("src", "main", "resources", "pgt", "cnv_view", "Data");
		if (Files.exists(projectData)) return projectData;
		return Paths.get(System.getProperty("user.dir"), "data");
	}
}

// Simple static holder to allow ScatterChart to access current ViewController without reintroducing old registry naming
class ViewControllerStaticRef {
    private static ViewController ref;
    static void set(ViewController vc) { ref = vc; }
    static ViewController get() { return ref; }
}
