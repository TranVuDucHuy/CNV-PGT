package pgt.cnv_view.controller;

import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.fxml.Initializable;
import javafx.scene.Parent;
import javafx.scene.control.ScrollPane;
import javafx.scene.control.MenuButton;
import javafx.scene.control.MenuItem;
import javafx.event.ActionEvent;
import javafx.scene.layout.VBox;
import javafx.scene.layout.Region;
import java.net.URL;
import java.util.*;

/**
 * Dynamically builds one or multiple scatter charts depending on selection:
 * - If user selected 2 samples (and only 1 algorithm enforced) -> show 2 charts (one per sample) stacked vertically.
 * - Else if user selected 2 algorithms (and 1 sample) -> show 2 charts (one per algorithm) stacked vertically.
 * - Else fallback to single normal ScatterChart.fxml.
 */
public class MultiScatterChartController implements Initializable {

    @FXML private ScrollPane rootScroll;
    @FXML private VBox chartsBox;
    @FXML private MenuButton dataMenu;
    @FXML private MenuButton chromosomeMenu;
    // Included report controller (fx:include fx:id="report" => field name reportController)
    @FXML private ReportController reportController;

    // Keep references to child chart controllers for updates
    private final List<ScatterChartController> childControllers = new ArrayList<>();
    private static final double BASE_CHART_WIDTH = 1040; // initial logical width before expanding

    @Override
    public void initialize(URL location, ResourceBundle resources) {
    ViewController vc = ViewControllerStaticRef.get();
    if (vc == null) return;
    // Use visual order (left pane order) rather than selection timestamp order
    List<String> samples = vc.getSelectedSampleNamesInDisplayOrder();
    List<String> algos = vc.getSelectedAlgorithmTokensInDisplayOrder();

        // Deduplicate while preserving selection order to avoid accidental duplicate charts
        LinkedHashSet<String> uniqueSampleSet = new LinkedHashSet<>(samples);
        List<String> uniqueSamples = new ArrayList<>(uniqueSampleSet);

        boolean multiSamples = uniqueSamples.size() >= 2 && algos.size() >= 1; // now supports 2..6 samples stacked
        boolean multiAlgosSingleSample = samples.size() == 1 && algos.size() >= 2; // still allow comparing algorithms for one sample

        if (!(multiSamples || multiAlgosSingleSample)) {
            addSingleChart(uniqueSamples.isEmpty() ? null : uniqueSamples.get(0), algos.isEmpty() ? null : algos.get(0));
            return;
        }

        if (multiSamples) {
            String algo = algos.get(0); // only first algorithm used when multiple samples selected
            for (String sample : uniqueSamples) {
                if (sample == null || sample.isBlank()) continue;
                addSingleChart(sample, algo);
            }
        } else if (multiAlgosSingleSample) {
            String sample = uniqueSamples.get(0);
            for (String algo : algos) addSingleChart(sample, algo);
        }
    // Load report after charts constructed
    if (reportController != null) reportController.refresh();
    // Setup responsive width after initial layout pass
    javafx.application.Platform.runLater(this::setupResponsiveWidthBinding);
    }

    private void addSingleChart(String sample, String algo) {
        try {
            FXMLLoader loader = new FXMLLoader(getClass().getResource("/pgt/cnv_view/FXML/ScatterChart.fxml"));
            Parent root = loader.load();
            // Top bar was removed from ScatterChart.fxml; just add the chart container directly
            chartsBox.getChildren().add(root);
            ScatterChartController ctrl = loader.getController();
            if (sample != null && algo != null && ctrl != null) {
                // Debug print to console (can remove later)
                System.out.println("[MultiScatter] Creating chart for sample=" + sample + ", algo=" + algo);
                ctrl.reloadWith(sample, algo);
            }
            if (ctrl != null) childControllers.add(ctrl);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @FXML
    private void onMenuItemSelected(ActionEvent event) {
        Object src = event.getSource();
        if (src instanceof MenuItem mi) {
            var popup = mi.getParentPopup();
            if (popup != null && popup.getOwnerNode() instanceof MenuButton mb) {
                mb.setText(mi.getText());
            }
            // Propagate chromosome filter (if this menu was chromosomeMenu)
            if (popup != null && popup.getOwnerNode() == chromosomeMenu) {
                String label = mi.getText();
                // Extract chromosome token
                String token = label.replace("Chromosome ", "").trim();
                if (token.equalsIgnoreCase("All chromosome")) token = null;
                for (ScatterChartController c : childControllers) {
                    c.setChromosome(token);
                }
            }
        }
    }

    private void setupResponsiveWidthBinding() {
        if (rootScroll == null || chartsBox == null) return;
        // Adjust widths when viewport changes (split pane drag / fullscreen)
        rootScroll.viewportBoundsProperty().addListener((obs, oldB, newB) -> {
            double vpW = newB.getWidth();
            double target = Math.max(BASE_CHART_WIDTH, vpW - 20); // minus padding
            for (var node : chartsBox.getChildren()) {
                if (node instanceof Region r) {
                    r.setPrefWidth(target);
                }
            }
        });
        // Run once with current viewport if available
        var vb = rootScroll.getViewportBounds();
        if (vb != null) {
            double vpW = vb.getWidth();
            double target = Math.max(BASE_CHART_WIDTH, vpW - 20);
            for (var node : chartsBox.getChildren()) {
                if (node instanceof Region r) r.setPrefWidth(target);
            }
        }
    }
}
