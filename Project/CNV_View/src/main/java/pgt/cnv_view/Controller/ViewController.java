package pgt.cnv_view.Controller;

import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.fxml.Initializable;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.CheckBox;
import javafx.scene.control.Tooltip;
import javafx.scene.layout.Region;
import javafx.scene.layout.VBox;
import javafx.scene.layout.StackPane;
import javafx.stage.Stage;


import java.io.IOException;
import java.net.URL;
import java.util.ResourceBundle;
import java.util.LinkedList;
import java.util.List;
import java.nio.file.*;

import javafx.event.ActionEvent;

public class ViewController implements Initializable {
    @FXML
    private StackPane contentArea;

    @FXML
    private VBox sampleContainer;

    // Store up to 2 selected sample checkboxes (FIFO behavior)
    private final List<CheckBox> selectedSamples = new LinkedList<>();

    @FXML
    private CheckBox baseline, bicSeq2, wisecondorX, blueFuse, scatterChart, boxPlot, dataTable, report;

    // Track up to 2 selected algorithm checkboxes (FIFO behavior)
    private final List<CheckBox> selectedAlgorithms = new LinkedList<>();

    @Override
    public void initialize(URL location, ResourceBundle resources) {
        disableCheckBoxes(true);
        addSelectionListeners();
    addViewGroupMutualExclusion();
    loadExistingSamples();
    // expose this instance for scatter chart
    try { ViewControllerStaticRef.set(this); } catch (NoClassDefFoundError ignored) {}
    }

    public void scatterChart(ActionEvent actionEvent) throws IOException {
    // Always load MultiScatterChart.fxml; controller will decide to render
    // one or multiple charts based on current selections.
    Parent fxml = FXMLLoader.load(getClass().getResource("/pgt/cnv_view/FXML/MultiScatterChart.fxml"));
    contentArea.getChildren().setAll(fxml);
    }

    public void dataTable(ActionEvent actionEvent) throws IOException {
        // Determine first selected sample + primary algorithm -> build bins file path
        if (selectedSamples.isEmpty() || selectedAlgorithms.isEmpty()) {
            return; // nothing to show
        }
        String sample = selectedSamples.get(0).getText();
        String algoToken = getPrimaryAlgorithmToken();
        if (algoToken == null) return;
        Path binsFile = resolveDataRoot()
                .resolve(sample)
                .resolve(algoToken)
                .resolve(sample + "_" + algoToken + "_bins.tsv");

        FXMLLoader loader = new FXMLLoader(getClass().getResource("/pgt/cnv_view/FXML/DataTable.fxml"));
        Parent root = loader.load();
        DataTableController ctrl = loader.getController();
        if (ctrl != null) {
            ctrl.loadBinsFile(binsFile);
        }
        contentArea.getChildren().setAll(root);
    }

    public void addSample(ActionEvent actionEvent) throws IOException {
        FXMLLoader loader = new FXMLLoader(getClass().getResource("/pgt/cnv_view/FXML/AddSample.fxml"));
        Parent root = loader.load();
        AddSampleController addSampleController = loader.getController();
        if (addSampleController != null) {
            addSampleController.setParentController(this);
        }
        Scene scene = new Scene(root);
        Stage stage = new Stage();
        stage.setTitle("Add Sample");
        stage.setScene(scene);
        stage.initModality(javafx.stage.Modality.APPLICATION_MODAL);
        stage.initOwner(contentArea.getScene().getWindow());
        stage.show();
    }


    private void setupSampleSelection(CheckBox sample) {
        sample.selectedProperty().addListener((obs, oldVal, newVal) -> {
            if (newVal) { // selecting
                if (!selectedSamples.contains(sample)) {
                    if (selectedSamples.size() == 2) {
                        // Remove (deselect) the oldest
                        CheckBox oldest = selectedSamples.remove(0);
                        oldest.setSelected(false); // this triggers its own listener to remove it
                    }
                    selectedSamples.add(sample);
                    if (!sample.getStyleClass().contains("selected")) {
                        sample.getStyleClass().add("selected");
                    }
                }
            } else { // deselecting
                selectedSamples.remove(sample);
                sample.getStyleClass().remove("selected");
            }

            // Enable / disable downstream checkboxes based on whether any sample is selected
            if (selectedSamples.isEmpty()) {
                disableCheckBoxes(true);
                resetCheckBoxes();
            } else {
                // When set grows (i.e., selecting new one), we can reset other groups
                if (newVal) {
                    resetCheckBoxes();
                }
                disableCheckBoxes(false);
                updateAlgorithmAvailability();
                checkFirstGroupSelection();
            }

            // Enforce dynamic algorithm selection limit (if 2 samples selected -> only 1 algorithm allowed)
            enforceAlgorithmLimit();
        });
    }

    private void disableCheckBoxes(boolean disable) {
        baseline.setDisable(disable);
        bicSeq2.setDisable(disable);
        wisecondorX.setDisable(disable);
        blueFuse.setDisable(disable);
        scatterChart.setDisable(disable);
        boxPlot.setDisable(disable);
        dataTable.setDisable(disable);
        report.setDisable(disable);
    }

    private void resetCheckBoxes() {
        baseline.setSelected(false);
        bicSeq2.setSelected(false);
        wisecondorX.setSelected(false);
        blueFuse.setSelected(false);
        scatterChart.setSelected(false);
        boxPlot.setSelected(false);
        dataTable.setSelected(false);
        report.setSelected(false);
    }

    private void addSelectionListeners() {
        addAlgorithmSelectionListener(baseline);
        addAlgorithmSelectionListener(bicSeq2);
        addAlgorithmSelectionListener(wisecondorX);
        addAlgorithmSelectionListener(blueFuse);
    }

    // Enforce maximum of 2 selected algorithm checkboxes
    private void addAlgorithmSelectionListener(CheckBox checkBox) {
        checkBox.selectedProperty().addListener((observable, oldVal, newVal) -> {
            if (newVal) { // selecting
                if (!selectedAlgorithms.contains(checkBox)) {
                    int limit = (selectedSamples.size() == 2) ? 1 : 2; // dynamic limit
                    if (selectedAlgorithms.size() == limit) {
                        // Deselect the oldest (FIFO) to respect current limit
                        CheckBox oldest = selectedAlgorithms.get(0);
                        oldest.setSelected(false); // triggers removal
                    }
                    selectedAlgorithms.add(checkBox);
                }
            } else { // deselecting
                selectedAlgorithms.remove(checkBox);
            }
            // Update state of second group depending on whether at least one algorithm is selected
            checkFirstGroupSelection();
            // Re-apply limit in case samples changed after this selection
            enforceAlgorithmLimit();
            // Recompute availability (in case deselect changed intersection)
            updateAlgorithmAvailability();
        });
    }

    // Ensure algorithm selection count respects dynamic limit (1 if 2 samples selected, else 2)
    private void enforceAlgorithmLimit() {
        int limit = (selectedSamples.size() == 2) ? 1 : 2;
        while (selectedAlgorithms.size() > limit) {
            CheckBox oldest = selectedAlgorithms.remove(0);
            if (oldest.isSelected()) {
                oldest.setSelected(false); // triggers deselection listener
            }
        }
    }

    private void checkFirstGroupSelection() {
        boolean atLeastOneSelected = baseline.isSelected() || bicSeq2.isSelected() || wisecondorX.isSelected() || blueFuse.isSelected();
        disableSecondGroupCheckBoxes(!atLeastOneSelected);
    }

    private void disableSecondGroupCheckBoxes(boolean disable) {
        scatterChart.setDisable(disable);
        boxPlot.setDisable(disable);
        dataTable.setDisable(disable);
        report.setDisable(disable);
    }

    // Ensure only one of the 4 view checkboxes can be selected at a time
    private void addViewGroupMutualExclusion() {
        addExclusiveListener(scatterChart, boxPlot, dataTable, report);
        addExclusiveListener(boxPlot, scatterChart, dataTable, report);
        addExclusiveListener(dataTable, scatterChart, boxPlot, report);
        addExclusiveListener(report, scatterChart, boxPlot, dataTable);
    }

    private void addExclusiveListener(CheckBox primary, CheckBox... others) {
        primary.selectedProperty().addListener((obs, oldVal, newVal) -> {
            if (newVal) { // when selected, unselect others
                for (CheckBox cb : others) {
                    if (cb.isSelected()) {
                        cb.setSelected(false);
                    }
                }
            }
        });
    }

    // Update which algorithms are selectable: an algorithm is enabled only if ALL selected samples have result files for it
    private void updateAlgorithmAvailability() {
        if (selectedSamples.isEmpty()) {
            // already handled elsewhere by disableCheckBoxes(true)
            return;
        }
        // Map algorithm checkbox to its token (must match normalization used when saving files)
        Object[][] algos = new Object[][]{
                {baseline, "baseline"},
                {bicSeq2, "bicseq2"},
                {wisecondorX, "wisecondorx"},
                {blueFuse, "bluefuse"}
        };
        List<String> sampleNames = selectedSamples.stream().map(CheckBox::getText).toList();
        for (Object[] entry : algos) {
            CheckBox cb = (CheckBox) entry[0];
            String token = (String) entry[1];
            boolean available = samplesHaveAlgorithm(sampleNames, token);
            cb.setDisable(!available);
            if (!available && cb.isSelected()) {
                cb.setSelected(false);
            }
        }
        // After possible deselections re-evaluate view group access
        checkFirstGroupSelection();
        enforceAlgorithmLimit();
    }

    private boolean samplesHaveAlgorithm(List<String> sampleNames, String algoToken) {
        for (String sample : sampleNames) {
            if (!sampleHasAlgorithm(sample, algoToken)) {
                return false;
            }
        }
        return true;
    }

    private boolean sampleHasAlgorithm(String sampleName, String algoToken) {
        try {
            Path dataRoot = resolveDataRoot();
            Path dir = dataRoot.resolve(sampleName).resolve(algoToken);
            if (!Files.isDirectory(dir)) return false;
            Path bins = dir.resolve(sampleName + "_" + algoToken + "_bins.tsv");
            Path segs = dir.resolve(sampleName + "_" + algoToken + "_segments.tsv");
            return Files.exists(bins) && Files.exists(segs);
        } catch (Exception e) {
            return false;
        }
    }

    // Scan data root to preload existing samples dynamically
    private void loadExistingSamples() {
        try {
            Path dataRoot = resolveDataRoot();
            if (!Files.exists(dataRoot) || !Files.isDirectory(dataRoot)) return;
            Files.list(dataRoot)
                    .filter(Files::isDirectory)
                    .map(p -> p.getFileName().toString())
                    .filter(this::sampleDirectoryHasAnyAlgorithm)
                    .sorted()
                    .forEach(this::addSampleCheckbox);
        } catch (Exception ignored) {}
    }

    private boolean sampleDirectoryHasAnyAlgorithm(String sampleName) {
        String[] algos = {"baseline", "bicseq2", "wisecondorx", "bluefuse"};
        for (String algo : algos) {
            if (sampleHasAlgorithm(sampleName, algo)) return true;
        }
        return false;
    }

    private Path resolveDataRoot() {
        Path projectData = Paths.get("src", "main", "resources", "pgt", "cnv_view", "Data");
        if (Files.exists(projectData)) return projectData;
        return Paths.get(System.getProperty("user.dir"), "data");
    }

    // Accessors for DataTable
    public List<String> getSelectedSampleNames() {
        return selectedSamples.stream().map(CheckBox::getText).toList();
    }

    public String getPrimaryAlgorithmToken() {
        if (selectedAlgorithms.isEmpty()) return null;
        CheckBox cb = selectedAlgorithms.get(0);
        String text = cb.getText().toLowerCase().replaceAll("\\s+", "");
        // unify mapping for bic-seq2 vs formatting
        if (text.contains("bic")) return "bicseq2";
        return text;
    }

    public List<String> getSelectedAlgorithmTokens() {
        List<String> tokens = new LinkedList<>();
        for (CheckBox cb : selectedAlgorithms) {
            String text = cb.getText().toLowerCase().replaceAll("\\s+", "");
            if (text.contains("bic")) text = "bicseq2";
            tokens.add(text);
        }
        return tokens;
    }

    // Called by AddSample controller after successful addition or detection of existing sample
    public void registerSample(String sampleName) {
        // Avoid duplicates
        for (CheckBox cb : getAllSampleCheckBoxes()) {
            if (cb.getText().equals(sampleName)) { updateAlgorithmAvailability(); return; }
        }
        addSampleCheckbox(sampleName);
        updateAlgorithmAvailability();
    }

    private void addSampleCheckbox(String sampleName) {
        CheckBox cb = new CheckBox(sampleName);
        // Let width expand to content; enables horizontal scrollbar instead of wrapping
        cb.setPrefWidth(Region.USE_COMPUTED_SIZE);
        cb.setMinWidth(Region.USE_PREF_SIZE);
        cb.setMaxWidth(Region.USE_COMPUTED_SIZE);
        cb.setWrapText(false);
        cb.setTooltip(new Tooltip(sampleName)); // hover shows full name anyway
        cb.getStyleClass().add("sample");
        sampleContainer.getChildren().add(cb);
        setupSampleSelection(cb);
    }

    private List<CheckBox> getAllSampleCheckBoxes() {
        List<CheckBox> list = new LinkedList<>();
        for (javafx.scene.Node n : sampleContainer.getChildren()) {
            if (n instanceof CheckBox c) list.add(c);
        }
        return list;
    }
}