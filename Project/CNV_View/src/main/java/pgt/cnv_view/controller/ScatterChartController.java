package pgt.cnv_view.controller;

import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.chart.NumberAxis;
import javafx.scene.chart.XYChart;
import javafx.scene.control.MenuButton;
import javafx.scene.control.Alert;
// removed unused ProgressIndicator & StackPane imports
import javafx.scene.shape.Line;
import java.nio.file.*;
import java.io.IOException;
import java.util.*;
import java.util.stream.Stream;
import javafx.scene.text.Text;
import javafx.geometry.VPos;
import javafx.application.Platform;
import javafx.scene.canvas.Canvas;
import javafx.scene.canvas.GraphicsContext;
import javafx.scene.paint.Color;

import java.net.URL;
import java.util.ResourceBundle;
import pgt.cnv_view.util.CnvData;
import javafx.util.StringConverter;

public class ScatterChartController implements Initializable {

	private static final double CANVAS_POINT_SIZE_MULTI = 2.0;
	private static final double CANVAS_POINT_SIZE_SINGLE = 3.0;
	// Colors by segment Type
	private static final Color COLOR_NO_CHANGE = Color.web("#25c225ff"); // green
	private static final Color COLOR_LOSS = Color.web("#1c60c5ff"); // blue
	private static final Color COLOR_GAIN = Color.web("#ce371cff"); // red
	// Separate segment colors (can differ from point colors for emphasis)
	private static final Color SEG_COLOR_NO_CHANGE = Color.web("#017a09ff"); // example: darker green
	private static final Color SEG_COLOR_LOSS = Color.web("#0241ffff"); // deeper blue
	private static final Color SEG_COLOR_GAIN = Color.web("#fe0101ff"); // deeper red
	private static final double POINT_OPACITY = 0.6; // requested opacity
	private static final double REF_LINE_WIDTH = 2.0; // thicker reference lines y=1 & y=3

	@FXML
	private MenuButton chromosomeMenu; // not used now
	@FXML
	private javafx.scene.chart.ScatterChart<Number, Number> chart;

	// Overrides for multi-chart rendering
	private String overrideSample;
	private String overrideAlgorithm;

	// Incrementing token to cancel stale async loads (sample/algo/chr changes)
	private volatile long loadGeneration = 0;

	// Optional chromosome filter ("1".."22","X","Y" or null for all)
	private String filteredChromosome; // null -> all

	// Showing all chromosomes simultaneously; removed single-chromosome state

	@Override
	public void initialize(URL location, ResourceBundle resources) {
		// Set default label
		if (chromosomeMenu != null) chromosomeMenu.setText("All Chromosomes");
		// Không tự load ở chế độ multi-chart để tránh race condition (tất cả controller ban đầu sẽ lấy mẫu đầu tiên)
		// MultiScatterChartController sẽ gọi reloadWith(sample, algo) cho từng chart.

		// Redraw segment overlays when chart resized or axis range changes
		if (chart != null) {
			Runnable r = this::scheduleRedrawSegments;
			chart.widthProperty().addListener((o,a,b)-> r.run());
			chart.heightProperty().addListener((o,a,b)-> r.run());
			chart.layoutBoundsProperty().addListener((o,a,b)-> r.run());
			chart.sceneProperty().addListener((o,oldV,newV)-> {
				if (newV!=null) Platform.runLater(() -> { attachAxisListenersIfNeeded(); r.run(); });
			});
		}
	}

	// External caller can force specific sample+algorithm then reload
	public void reloadWith(String sample, String algorithmToken) {
		this.overrideSample = sample;
		this.overrideAlgorithm = algorithmToken;
		loadAndPlot();
	}

	public void setChromosome(String chr) {
		// Normalize: accept null or already normalized tokens
		String norm = (chr == null || chr.isBlank() || chr.equalsIgnoreCase("all chromosome") || chr.equalsIgnoreCase("all chromosomes")) ? null : chr.replaceFirst("^(?i)chr", "").toUpperCase();
		if (Objects.equals(this.filteredChromosome, norm)) return; // no change
		this.filteredChromosome = norm;
		loadAndPlot();
	}

	private boolean axisListenersAttached = false;
	private void attachAxisListenersIfNeeded() {
		if (axisListenersAttached) return;
		if (chart == null) return;
		// Axes nodes exist after first CSS/layout pass
		var xAxis = chart.getXAxis();
		var yAxis = chart.getYAxis();
		if (xAxis instanceof NumberAxis nx) {
			nx.lowerBoundProperty().addListener((o,a,b)-> scheduleRedrawSegments());
			nx.upperBoundProperty().addListener((o,a,b)-> scheduleRedrawSegments());
		}
		if (yAxis instanceof NumberAxis ny) {
			ny.lowerBoundProperty().addListener((o,a,b)-> scheduleRedrawSegments());
			ny.upperBoundProperty().addListener((o,a,b)-> scheduleRedrawSegments());
		}
		var plotBg = chart.lookup(".chart-plot-background");
		if (plotBg != null) {
			plotBg.boundsInParentProperty().addListener((o,a,b)-> scheduleRedrawSegments());
		}
		// Window (Stage) resize -> fullscreen / normal toggle
		if (chart.getScene() != null) {
			chart.getScene().windowProperty().addListener((o,a,b)-> {
				if (b instanceof javafx.stage.Stage st) {
					st.fullScreenProperty().addListener((obs,ov,nv)-> scheduleRedrawSegments());
					st.widthProperty().addListener((obs,ov,nv)-> scheduleRedrawSegments());
					st.heightProperty().addListener((obs,ov,nv)-> scheduleRedrawSegments());
				}
			});
		}
		axisListenersAttached = true;
	}

	private void scheduleRedrawSegments() {
		// Double runLater đảm bảo layout sau resize hoàn tất (fullscreen thay đổi lớn)
		Platform.runLater(() -> Platform.runLater(this::redrawSegments));
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
		long myGen = ++loadGeneration; // new load cycle id
		List<String> samples;
		String algo;
		if (overrideSample != null && overrideAlgorithm != null) {
			samples = List.of(overrideSample);
			algo = overrideAlgorithm;
		} else {
			samples = vc.getSelectedSampleNames();
			algo = vc.getPrimaryAlgorithmToken();
		}
		if (samples == null || samples.isEmpty() || algo == null) return;
		String sample = samples.get(0);
		// Pre-set a provisional title while loading
		chart.setTitle(buildTitle(sample, algo, filteredChromosome));
		Path binsFile = resolveDataRoot()
				.resolve(sample)
				.resolve(algo)
				.resolve(sample + "_" + algo + "_bins.tsv");
		if (!Files.exists(binsFile)) return;

		// Load data asynchronously to avoid UI freezing
		loadDataAsync(binsFile, sample, algo, myGen);
	}

	private List<Segment> currentSegments = Collections.emptyList();
	// Categorized point lists (genomic x, copy) after classification by segment Type
	private List<double[]> fastPointsNoChange = Collections.emptyList();
	private List<double[]> fastPointsLoss = Collections.emptyList();
	private List<double[]> fastPointsGain = Collections.emptyList();
	private Map<String, Long> currentChromOffset = Collections.emptyMap();
	private Map<String, Long> currentChromLength = Collections.emptyMap();
	private List<String> chromosomeOrder = List.of();
	private long currentGenomeTotal = 0L;

	private void loadDataAsync(Path binsFile, String sample, String algoForThread, long gen) {
		// Run data loading in background thread
		new Thread(() -> {
			try {
				List<String> chromList = CnvData.CHROMOSOMES; // standardized list
				String filterChr = filteredChromosome; // snapshot (race guard)
				Map<String, List<long[]>> points = new HashMap<>(); // long[]{start, copyBits}
				Map<String, Long> chromMax = new HashMap<>(); // use max END (col2) else start
				List<Segment> segments = new ArrayList<>();
				Map<String, List<Segment>> segmentsByChr = new HashMap<>();

				try (Stream<String> lines = Files.lines(binsFile)) {
					lines.skip(1).filter(l -> !l.isBlank()).forEach(line -> {
						String[] p = line.split("\t");
						if (p.length < 4) return;
						String chrRaw = p[0];
						String chr = chrRaw.replaceFirst("^(?i)chr", "");
						if (!chromList.contains(chr)) return;
						if (filterChr != null && !chr.equalsIgnoreCase(filterChr)) return; // skip non-selected chromosomes
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
				}

				// Parse segments file (optional) — must match the algorithm of this chart, not global primary
				Path segmentsFile = binsFile.getParent().resolve(sample + "_" + algoForThread + "_segments.tsv");
				if (Files.exists(segmentsFile)) {
					try (Stream<String> lines = Files.lines(segmentsFile)) {
						lines.skip(1).filter(l -> !l.isBlank()).forEach(line -> {
							String[] p = line.split("\t");
							if (p.length < 4) return; // need at least chr start end copy
							String chr = p[0].replaceFirst("^(?i)chr", "");
							if (!chromList.contains(chr)) return;
							if (filterChr != null && !chr.equalsIgnoreCase(filterChr)) return;
							try {
								long start = Long.parseLong(p[1]);
								long end = parseLongSafe(p[2], start);
								double copy = Double.parseDouble(p[3]);
								String type = (p.length > 4 ? p[4] : "");
								Segment seg = new Segment(chr, start, end, copy, type);
								segments.add(seg);
								segmentsByChr.computeIfAbsent(chr, k -> new ArrayList<>()).add(seg);
							} catch (NumberFormatException ignored) {}
						});
					} catch (IOException ignored) {}
				}
				// Sort each chr's segments for binary search classification
				for (List<Segment> lst : segmentsByChr.values()) lst.sort(Comparator.comparingLong(a -> a.start));

				// Total length (sum of chrom lengths with data)
				long totalLen = chromMax.values().stream().mapToLong(Long::longValue).sum();
				if (totalLen <= 0) return;

				// No sampling - show all points to preserve small CNV anomalies
				// This is critical for CNV analysis where small variations matter
				
				int totalPoints = points.values().stream().mapToInt(List::size).sum();
				List<double[]> fastPointsLocal = new ArrayList<>(totalPoints); // all points (for legacy use)
				List<double[]> ptsNoChange = new ArrayList<>();
				List<double[]> ptsLoss = new ArrayList<>();
				List<double[]> ptsGain = new ArrayList<>();

				// Build cumulative offsets proportional to length; normalize to 0..totalLen
				long cumulative = 0;
				Map<String, Long> chromOffset = new HashMap<>();
				if (filterChr == null) {
					for (String chr : chromList) {
						Long len = chromMax.get(chr);
						if (len == null) continue;
						chromOffset.put(chr, cumulative);
						List<long[]> lst = points.get(chr);
						if (lst != null) {
							List<Segment> segs = segmentsByChr.get(chr);
							for (long[] arr : lst) {
								long start = arr[0];
								double copy = Double.longBitsToDouble(arr[1]);
								double x = cumulative + (double) start;
								fastPointsLocal.add(new double[]{x, copy});
								String typeNorm = classify(start, segs);
								if (typeNorm.equals("loss")) ptsLoss.add(new double[]{x, copy});
								else if (typeNorm.equals("gain")) ptsGain.add(new double[]{x, copy});
								else ptsNoChange.add(new double[]{x, copy});
							}
						}
						cumulative += len;
					}
				} else {
					// Single chromosome: offset 0
					Long len = chromMax.get(filterChr);
					if (len != null) {
						chromOffset.put(filterChr, 0L);
						List<long[]> lst = points.get(filterChr);
						if (lst != null) {
							List<Segment> segs = segmentsByChr.get(filterChr);
							for (long[] arr : lst) {
								long start = arr[0];
								double copy = Double.longBitsToDouble(arr[1]);
								fastPointsLocal.add(new double[]{(double) start, copy});
								String typeNorm = classify(start, segs);
								if (typeNorm.equals("loss")) ptsLoss.add(new double[]{(double) start, copy});
								else if (typeNorm.equals("gain")) ptsGain.add(new double[]{(double) start, copy});
								else ptsNoChange.add(new double[]{(double) start, copy});
							}
						}
					}
				}

				// no node series population

				// Update UI on JavaFX Application Thread
				Platform.runLater(() -> {
					// Clear existing data and show loading state
					chart.getData().clear();
					chart.setTitle("Loading data...");
				});
				
				// Process data...
				// Update UI on JavaFX Application Thread
				// Store for redraws
				currentSegments = segments;
				currentChromOffset = chromOffset;
				currentChromLength = chromMax;
				chromosomeOrder = (filterChr == null ? chromList.stream().filter(chromMax::containsKey).toList() : (chromMax.containsKey(filterChr) ? List.of(filterChr) : List.of()));
				currentGenomeTotal = totalLen;
				final List<double[]> finalFastPoints = fastPointsLocal; // all points (legacy)
				final List<double[]> finalPtsNoChange = ptsNoChange;
				final List<double[]> finalPtsLoss = ptsLoss;
				final List<double[]> finalPtsGain = ptsGain;

				Platform.runLater(() -> {
					// Race guard: generation + overrides + chromosome filter must still match
					if (gen != loadGeneration) return; // superseded by a newer request
					if (overrideSample != null && !Objects.equals(overrideSample, sample)) return; // outdated sample
					if (overrideAlgorithm != null && !Objects.equals(overrideAlgorithm, algoForThread)) return; // outdated algo
					if (!Objects.equals(filteredChromosome, filterChr)) return; // chromosome changed
					chart.setTitle(buildTitle(sample, algoTokenForTitle(), filterChr));
					chart.getData().add(new XYChart.Series<>()); // minimal empty series for axes
					// Always hide legend to maximize vertical space & avoid overlap
					chart.setLegendVisible(false);

					configureAndForceXAxis(filterChr, chromMax, totalLen);

					// Trigger canvas drawing after layout
					Platform.runLater(() -> {
						// Ensure axis layout updated before drawing points to avoid stale scaling
						chart.applyCss();
						chart.layout();
						setupFastCanvasIfNeeded();
						fastPoints = finalFastPoints; // legacy store
						fastPointsNoChange = finalPtsNoChange;
						fastPointsLoss = finalPtsLoss;
						fastPointsGain = finalPtsGain;
						drawFastPoints();
					});

					if (!segments.isEmpty()) {
						Platform.runLater(this::redrawSegments); // layout then draw
					}
				});

			} catch (IOException e) {
				Platform.runLater(() -> {
					new Alert(Alert.AlertType.ERROR, "Cannot load chart data: " + e.getMessage()).showAndWait();
				});
			}
		}, "ChartDataLoader").start();
	}

	private void redrawSegments() {
		if (!(chart.getXAxis() instanceof NumberAxis xAxis) || !(chart.getYAxis() instanceof NumberAxis yAxis)) return;
		var bg = chart.lookup(".chart-plot-background");
		if (bg == null) return;
		var plotArea = bg.getParent(); // StackPane containing background + series
		if (!(plotArea instanceof javafx.scene.layout.Pane pane)) return; // need pane for child overlay modifications
		// reference pane explicitly (no-op) to satisfy compiler if future refactors remove usages
		@SuppressWarnings("unused") javafx.scene.layout.Pane _paneRef = pane;

		// Hide default grid lines (vertical & horizontal) so only our custom overlays show
		chart.lookupAll(".chart-vertical-grid-lines").forEach(node -> node.setVisible(false));
		chart.lookupAll(".chart-vertical-zero-line").forEach(node -> node.setVisible(false));
		chart.lookupAll(".chart-horizontal-grid-lines").forEach(node -> node.setVisible(false));
		chart.lookupAll(".chart-horizontal-zero-line").forEach(node -> node.setVisible(false));

		// Bounds of background within the plotArea (offset due to padding / axis)
		var bgBounds = bg.getBoundsInParent();
		double offsetX = bgBounds.getMinX();
		double offsetY = bgBounds.getMinY();

		// Remove old segment, reference, chromosome boundary lines & labels
		pane.getChildren().removeIf(n -> {
			Object seg = n.getProperties().get("segmentLine");
			Object ref = n.getProperties().get("refLine");
			Object bLine = n.getProperties().get("chrBoundaryLine");
			Object lbl = n.getProperties().get("chrLabel");
			Object aux = n.getProperties().get("auxHLine");
			return (seg instanceof Boolean b1 && b1) || (ref instanceof Boolean b2 && b2) || (bLine instanceof Boolean b3 && b3) || (lbl instanceof Boolean b4 && b4) || (aux instanceof Boolean b5 && b5);
		});

		// Custom auxiliary horizontal lines (bolder) for intermediate ticks excluding reference lines y=1 & y=3
		double xStartAll = offsetX + xAxis.getDisplayPosition(xAxis.getLowerBound());
		double xEndAll = offsetX + xAxis.getDisplayPosition(xAxis.getUpperBound());
		for (var tick : yAxis.getTickMarks()) {
			double val = tick.getValue().doubleValue();
			if (Math.abs(val - 1.0) < 1e-6 || Math.abs(val - 3.0) < 1e-6 || Math.abs(val - 0.0) < 1e-6 || Math.abs(val - 4.0) < 1e-6) continue; // skip ref & excluded lines (0,1,3,4)
			double y = offsetY + yAxis.getDisplayPosition(val);
			if (Double.isNaN(y)) continue;
			Line auxLine = new Line(xStartAll, y, xEndAll, y);
			auxLine.getProperties().put("auxHLine", true);
			auxLine.setManaged(false);
			auxLine.setMouseTransparent(true);
			auxLine.setStrokeWidth(1.2); // slightly thicker
			auxLine.setStyle("-fx-stroke: #858585ff; -fx-opacity: 0.8; -fx-stroke-dash-array: 5 10;"); // dashed auxiliary line
			pane.getChildren().add(auxLine);
		}

		// Chromosome boundary + labels only in multi-chrom mode
		if (filteredChromosome == null && !chromosomeOrder.isEmpty() && currentGenomeTotal > 0) {
			for (int i=0;i<chromosomeOrder.size()-1;i++) {
				String chr = chromosomeOrder.get(i);
				Long startOffset = currentChromOffset.get(chr);
				Long len = currentChromLength.get(chr);
				if (startOffset==null || len==null) continue;
				double boundaryVal = startOffset + len; // end position of chr
				double x = offsetX + xAxis.getDisplayPosition(boundaryVal);
				if (Double.isNaN(x)) continue;
				Line vLine = new Line(x, offsetY + yAxis.getDisplayPosition(yAxis.getLowerBound()), x, offsetY + yAxis.getDisplayPosition(yAxis.getUpperBound()));
				vLine.getProperties().put("chrBoundaryLine", true);
				vLine.setManaged(false);
				vLine.setMouseTransparent(true);
				vLine.setStrokeWidth(1.0);
				vLine.setStyle("-fx-stroke: #4e4e4eff; -fx-opacity: 0.9;");
				pane.getChildren().add(vLine);
			}

			// Labels centered between boundaries
			List<Text> texts = new ArrayList<>();
			for (int i=0;i<chromosomeOrder.size();i++) {
				String chr = chromosomeOrder.get(i);
				Long startOffset = currentChromOffset.get(chr);
				Long len = currentChromLength.get(chr);
				if (startOffset==null || len==null) continue;
				// midpoint boundaries
				// Midpoint of current chromosome for label placement
				long chrMid = startOffset + len/2;
				double midX = offsetX + xAxis.getDisplayPosition(chrMid);
				if (Double.isNaN(midX)) continue;
				Text t = new Text(chr);
				t.getProperties().put("chrLabel", true);
				t.setManaged(false);
				t.setMouseTransparent(true);
				t.setTextOrigin(VPos.TOP);
				t.setStyle("-fx-fill: #222; -fx-font-size: 11px; -fx-font-weight: bold; -fx-opacity:0.9;");
				// provisional x (will adjust after layout to center exactly)
				t.setX(midX - 6);
				// Place label BELOW axis: use bottom of plot background + small margin
				double yLabel = offsetY + bgBounds.getHeight() + 4;
				t.setY(yLabel);
				pane.getChildren().add(t);
				texts.add(t);
			}
			// Fine centering after layout pass
			if (!texts.isEmpty()) {
				Platform.runLater(() -> {
					for (Text t : texts) {
						String chr = t.getText();
						Long startOffset = currentChromOffset.get(chr);
						Long len = currentChromLength.get(chr);
						if (startOffset==null || len==null) continue;
						double midX = offsetX + xAxis.getDisplayPosition(startOffset + len/2.0);
						if (!Double.isNaN(midX)) {
							double w = t.getLayoutBounds().getWidth();
							t.setX(midX - w/2.0);
						}
					}
				});
			}
		}

		// Draw horizontal reference lines FIRST so they appear behind points & segments
		double xStart = offsetX + xAxis.getDisplayPosition(xAxis.getLowerBound());
		double xEnd = offsetX + xAxis.getDisplayPosition(xAxis.getUpperBound());
		int canvasIndex = -1;
		if (fastCanvas != null) canvasIndex = pane.getChildren().indexOf(fastCanvas);
		double[] refYVals = {1.0, 3.0};
		for (double refVal : refYVals) {
			if (refVal < yAxis.getLowerBound() || refVal > yAxis.getUpperBound()) continue;
			double y = offsetY + yAxis.getDisplayPosition(refVal);
			if (Double.isNaN(y)) continue;
			Line refLine = new Line(xStart, y, xEnd, y);
			refLine.getProperties().put("refLine", true);
			refLine.setManaged(false);
			refLine.setMouseTransparent(true);
			refLine.setStrokeWidth(REF_LINE_WIDTH);
			String color = (refVal == 3.0) ? "#ff2600ff" : "#00aeffff"; // y=3 -> red, y=1 -> blue
			refLine.setStyle("-fx-stroke: " + color + "; -fx-stroke-dash-array: 5 10; -fx-opacity: 0.9;");
			if (canvasIndex >= 0) pane.getChildren().add(canvasIndex, refLine); else pane.getChildren().add(0, refLine);
		}

		// Draw CNV segments (after reference lines, above them)
		if (!currentSegments.isEmpty()) {
			for (Segment s : currentSegments) {
				Long cOff = currentChromOffset.get(s.chr);
				if (cOff == null) continue;
				double startVal = cOff + s.start;
				double endVal = cOff + s.end;
				if (startVal > xAxis.getUpperBound() || endVal < xAxis.getLowerBound()) continue; // out of range
				double x1 = offsetX + xAxis.getDisplayPosition(startVal);
				double x2 = offsetX + xAxis.getDisplayPosition(endVal);
				double y = offsetY + yAxis.getDisplayPosition(s.copy);
				if (Double.isNaN(x1) || Double.isNaN(x2) || Double.isNaN(y)) continue;
				Line line = new Line(x1, y, x2, y);
				line.getProperties().put("segmentLine", true);
				line.setManaged(false);
				line.setMouseTransparent(true);
				line.setStrokeWidth(4.0);
				String colorCss = switch (s.typeNormalized) {
					case "loss" -> toRgbaCss(SEG_COLOR_LOSS);
					case "gain" -> toRgbaCss(SEG_COLOR_GAIN);
					default -> toRgbaCss(SEG_COLOR_NO_CHANGE);
				};
				line.setStyle("-fx-stroke: " + colorCss + "; -fx-opacity: 1;");
				pane.getChildren().add(line);
			}
		}
		// Fast mode canvas redraw (points) after overlays updated
		if (fastCanvas != null && fastCanvas.isVisible()) {
			drawFastPoints();
		}
	}

	// ---------------- Fast Canvas Rendering -----------------
	private Canvas fastCanvas; // overlay canvas
	private List<double[]> fastPoints = Collections.emptyList(); // legacy combined list (not color-classified)

	private void setupFastCanvasIfNeeded() {
		if (fastCanvas != null) return;
		var bg = chart.lookup(".chart-plot-background");
		if (bg == null) return;
		var plotArea = bg.getParent();
		if (!(plotArea instanceof javafx.scene.layout.Pane pane)) return;
		fastCanvas = new Canvas();
		fastCanvas.getProperties().put("fastCanvas", true);
		fastCanvas.setMouseTransparent(true);
		pane.getChildren().add(fastCanvas);
		// Listeners to resize canvas with plot area
		pane.layoutBoundsProperty().addListener((o,a,b)-> positionAndResizeFastCanvas());
	}

	private void positionAndResizeFastCanvas() {
		if (fastCanvas == null) return;
		var bg = chart.lookup(".chart-plot-background");
		if (bg == null) return;
		var plotArea = bg.getParent();
		if (!(plotArea instanceof javafx.scene.layout.Pane)) return;
		var bgBounds = bg.getBoundsInParent();
		fastCanvas.setLayoutX(bgBounds.getMinX());
		fastCanvas.setLayoutY(bgBounds.getMinY());
		double w = Math.max(1, bgBounds.getWidth());
		double h = Math.max(1, bgBounds.getHeight());
		if (fastCanvas.getWidth() != w || fastCanvas.getHeight() != h) {
			fastCanvas.setWidth(w);
			fastCanvas.setHeight(h);
		}
	}

	private void drawFastPoints() {
		if (fastCanvas == null || fastPoints == null) return;
		if (!(chart.getXAxis() instanceof NumberAxis xAxis) || !(chart.getYAxis() instanceof NumberAxis yAxis)) return;
		positionAndResizeFastCanvas();
		fastCanvas.setVisible(true);
		GraphicsContext g = fastCanvas.getGraphicsContext2D();
		g.clearRect(0,0, fastCanvas.getWidth(), fastCanvas.getHeight());
		g.setGlobalAlpha(POINT_OPACITY);
		// Determine scaling: map data x to display position then subtract lower bound position to fit canvas
		double lowerBoundX = xAxis.getLowerBound();
		double upperBoundX = xAxis.getUpperBound();
		double lbDisplay = xAxis.getDisplayPosition(lowerBoundX); // should be 0 within background
		double ubDisplay = xAxis.getDisplayPosition(upperBoundX);
		double spanDisplay = ubDisplay - lbDisplay;
		double lowerBoundY = yAxis.getLowerBound();
		double upperBoundY = yAxis.getUpperBound();
		if (spanDisplay == 0) return;
		// Draw with size depending on single/multi chromosome view
		double size = (filteredChromosome == null ? CANVAS_POINT_SIZE_MULTI : CANVAS_POINT_SIZE_SINGLE);
		drawPointList(g, xAxis, yAxis, fastPointsNoChange, COLOR_NO_CHANGE, size, lowerBoundX, upperBoundX, lowerBoundY, upperBoundY);
		drawPointList(g, xAxis, yAxis, fastPointsLoss, COLOR_LOSS, size, lowerBoundX, upperBoundX, lowerBoundY, upperBoundY);
		drawPointList(g, xAxis, yAxis, fastPointsGain, COLOR_GAIN, size, lowerBoundX, upperBoundX, lowerBoundY, upperBoundY);
	}

	private void drawPointList(GraphicsContext g, NumberAxis xAxis, NumberAxis yAxis, List<double[]> pts, Color c, double size, double lowerBoundX, double upperBoundX, double lowerBoundY, double upperBoundY) {
		if (pts == null || pts.isEmpty()) return;
		g.setFill(c);
		for (double[] pt : pts) {
			double xVal = pt[0];
			if (xVal < lowerBoundX || xVal > upperBoundX) continue;
			double yVal = pt[1];
			if (yVal < lowerBoundY || yVal > upperBoundY) continue;
			double x = xAxis.getDisplayPosition(xVal);
			double y = yAxis.getDisplayPosition(yVal);
			if (Double.isNaN(x) || Double.isNaN(y)) continue;
			g.fillOval(x - size/2, y - size/2, size, size);
		}
	}

	private String classify(long pos, List<Segment> segs) {
		if (segs == null || segs.isEmpty()) return "no_change";
		int lo = 0, hi = segs.size()-1;
		while (lo <= hi) {
			int mid = (lo+hi)/2;
			Segment s = segs.get(mid);
			if (pos < s.start) hi = mid - 1;
			else if (pos > s.end) lo = mid + 1;
			else return s.typeNormalized;
		}
		return "no_change";
	}

	private static class Segment {
		final String chr; final long start; final long end; final double copy; final String typeRaw; final String typeNormalized;
		Segment(String chr, long start, long end, double copy, String typeRaw) {
			this.chr = chr; this.start = start; this.end = end; this.copy = copy; this.typeRaw = typeRaw == null ? "" : typeRaw;
			String t = this.typeRaw.trim().toLowerCase(Locale.ROOT);
			if (t.equals("loss") || t.equals("del") || t.equals("deletion") || t.equals("loh")) this.typeNormalized = "loss";
			else if (t.equals("gain") || t.equals("dup") || t.equals("duplication") || t.equals("amp") || t.equals("amplification")) this.typeNormalized = "gain";
			else this.typeNormalized = "no_change";
		}
	}

	private static String toRgbaCss(Color c) {
		int r = (int)Math.round(c.getRed()*255);
		int g = (int)Math.round(c.getGreen()*255);
		int b = (int)Math.round(c.getBlue()*255);
		int a = (int)Math.round(c.getOpacity()*255);
		return String.format("#%02x%02x%02x%02x", r,g,b,a);
	}

	private long parseLongSafe(String s, long fallback) {
		try { return Long.parseLong(s); } catch (NumberFormatException e) { return fallback; }
	}


	private Path resolveDataRoot() { return CnvData.resolveDataRoot(); }

	// ---- Title helpers ----
	private String buildTitle(String sample, String algoToken, String chrFilter) {
		String algoPretty = prettyAlgorithm(algoToken);
		String chrPart = (chrFilter == null ? "All chromosomes" : "Chromosome " + chrFilter);
		String displaySample = CnvData.displaySampleName(sample);
		return displaySample + " -- " + algoPretty + " -- " + chrPart;
	}

	private String algoTokenForTitle() {
		if (overrideAlgorithm != null) return overrideAlgorithm;
		ViewController vc = ViewControllerStaticRef.get();
		return vc == null ? "" : vc.getPrimaryAlgorithmToken();
	}

	private String prettyAlgorithm(String token) { return CnvData.prettyAlgorithm(token); }

	// Ensure consistent axis range & tick calculation when switching chromosomes (fix scale bug after switching 1 -> 8)
	private void configureAndForceXAxis(String filterChr, Map<String, Long> chromMax, long totalLen) {
		if (!(chart.getXAxis() instanceof NumberAxis xAxis)) return;
		xAxis.setAutoRanging(false);
		xAxis.setLowerBound(0);
		long ub = (filterChr == null ? totalLen : chromMax.getOrDefault(filterChr, totalLen));
		if (ub <= 0) ub = 1; // avoid zero-range
		xAxis.setUpperBound(ub);
		if (!xAxis.getLabel().isBlank() && xAxis.getUserData() == null) xAxis.setUserData(xAxis.getLabel());
		xAxis.setLabel("");
		if (filterChr == null) {
			// multi-chromosome view
			xAxis.setTickLabelsVisible(false);
			xAxis.setMinorTickVisible(false);
			xAxis.setTickMarkVisible(false);
			xAxis.setTickUnit(Math.max(1, ub / 20.0));
		} else {
			// Single chromosome view: show genomic position in Mb (rounded), ticks every 25 Mb
			xAxis.setTickLabelsVisible(true);
			xAxis.setTickMarkVisible(true);
			xAxis.setMinorTickVisible(false);
			final double mb = 1_000_000d;
			final double desiredStepMb = 25d; // 25 Mb step asked by user
			double stepBp = desiredStepMb * mb;
			// Fallback if chromosome shorter than one step: aim ~5 ticks
			if (ub < stepBp) {
				stepBp = Math.max(1, Math.ceil(ub / 5.0));
			}
			xAxis.setTickUnit(stepBp);
			xAxis.setTickLabelFormatter(new StringConverter<Number>() {
				@Override public String toString(Number object) { return Long.toString(Math.round(object.doubleValue() / mb)); }
				@Override public Number fromString(String string) {
					try { return Long.parseLong(string) * (long) mb; } catch (NumberFormatException e) { return 0; }
				}
			});
		}
		// Force layout recalculation early so later canvas draw uses fresh scale
		chart.applyCss();
		chart.layout();
	}
}

// Simple static holder to allow ScatterChart to access current ViewController without reintroducing old registry naming
class ViewControllerStaticRef {
    private static ViewController ref;
    static void set(ViewController vc) { ref = vc; }
    static ViewController get() { return ref; }
}
