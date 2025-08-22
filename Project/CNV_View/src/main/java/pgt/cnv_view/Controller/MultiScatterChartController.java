package pgt.cnv_view.Controller;

import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.fxml.Initializable;
import javafx.scene.Parent;
import javafx.scene.control.ScrollPane;
import javafx.scene.control.MenuButton;
import javafx.scene.control.MenuItem;
import javafx.event.ActionEvent;
import javafx.scene.layout.VBox;
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

    // Keep references to child chart controllers for updates
    private final List<ScatterChartController> childControllers = new ArrayList<>();

    @Override
    public void initialize(URL location, ResourceBundle resources) {
        ViewController vc = ViewControllerStaticRef.get();
        if (vc == null) return;
    List<String> samples = vc.getSelectedSampleNames();
    List<String> algos = vc.getSelectedAlgorithmTokens();

    boolean twoSamples = samples.size() == 2 && algos.size() >= 1; // limit already enforced elsewhere
    boolean twoAlgos = samples.size() == 1 && algos.size() == 2;

        if (!(twoSamples || twoAlgos)) {
            // Fallback: load single chart fxml for current primary selection
            addSingleChart(samples.isEmpty() ? null : samples.get(0), algos.isEmpty()? null : algos.get(0));
            return;
        }

        if (twoSamples) {
            String algo = algos.get(0);
            for (String sample : samples) addSingleChart(sample, algo);
        } else if (twoAlgos) {
            String sample = samples.get(0);
            for (String algo : algos) addSingleChart(sample, algo);
        }
    }

    private void addSingleChart(String sample, String algo) {
        try {
            FXMLLoader loader = new FXMLLoader(getClass().getResource("/pgt/cnv_view/FXML/ScatterChart.fxml"));
            Parent root = loader.load();
            // Top bar was removed from ScatterChart.fxml; just add the chart container directly
            chartsBox.getChildren().add(root);
            ScatterChartController ctrl = loader.getController();
            if (sample != null && algo != null && ctrl != null) ctrl.reloadWith(sample, algo);
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
}
