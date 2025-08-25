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
import pgt.cnv_view.util.CnvData;

import javafx.event.ActionEvent;

public class ViewController implements Initializable {
    @FXML
    private StackPane contentArea;

    @FXML
    private VBox sampleContainer;

    // Store up to 6 selected sample checkboxes (FIFO behavior)
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
        attachUnifiedViewListeners();
    }

    private enum ViewType { SCATTER, DATATABLE, BOX, REPORT, NONE }
    private ViewType currentView = ViewType.NONE;

    public void scatterChart(ActionEvent actionEvent) throws IOException {
        // Delegate to unified refresh (selection state already changed)
        refreshViewContent();
    }

    public void dataTable(ActionEvent actionEvent) throws IOException {
        refreshViewContent();
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
                    if (selectedSamples.size() == 6) { // limit increased from 2 -> 6
                        // Remove (deselect) the oldest to maintain cap
                        CheckBox oldest = selectedSamples.remove(0);
                        oldest.setSelected(false); // triggers its listener
                    }
                    selectedSamples.add(sample);
                    if (!sample.getStyleClass().contains("selected")) sample.getStyleClass().add("selected");
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

            // Enforce dynamic algorithm selection limit (if >=2 samples selected -> only 1 algorithm allowed)
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

    // Enforce maximum algorithms (4 if single sample, else 1 when multiple samples)
    private void addAlgorithmSelectionListener(CheckBox checkBox) {
        checkBox.selectedProperty().addListener((observable, oldVal, newVal) -> {
            if (oldVal == newVal) return; // no change
            if (newVal) { // selecting
                if (!selectedAlgorithms.contains(checkBox)) {
                    int limit = (selectedSamples.size() >= 2) ? 1 : 4; // single sample -> up to 4 algos, multi-sample -> 1
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
            // Reset view selection & content because algorithm context changed (user or logic)
            resetViewSelection();
        });
    }

    private void resetViewSelection() {
        if (scatterChart != null) scatterChart.setSelected(false);
        if (boxPlot != null) boxPlot.setSelected(false);
        if (dataTable != null) dataTable.setSelected(false);
        if (report != null) report.setSelected(false);
        contentArea.getChildren().clear();
        currentView = ViewType.NONE;
    }

    // Ensure algorithm selection count respects dynamic limit (1 if >=2 samples selected, else 4)
    private void enforceAlgorithmLimit() {
        int limit = (selectedSamples.size() >= 2) ? 1 : 4;
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

    // Unified selection listeners for all view checkboxes
    private void attachUnifiedViewListeners() {
        if (scatterChart != null) scatterChart.selectedProperty().addListener((o, ov, nv) -> refreshViewContent());
        if (dataTable != null) dataTable.selectedProperty().addListener((o, ov, nv) -> refreshViewContent());
        if (boxPlot != null) boxPlot.selectedProperty().addListener((o, ov, nv) -> refreshViewContent());
        if (report != null) report.selectedProperty().addListener((o, ov, nv) -> refreshViewContent());
    }

    private void refreshViewContent() {
        ViewType desired = determineDesiredView();
        if (desired == ViewType.NONE) {
            if (currentView != ViewType.NONE) {
                contentArea.getChildren().clear();
                currentView = ViewType.NONE;
            }
            return;
        }
        if (desired == currentView) {
            // Still ensure prerequisites (e.g., data) else clear
            if (desired == ViewType.DATATABLE && !canShowDataTable()) {
                contentArea.getChildren().clear();
                currentView = ViewType.NONE;
            }
            return; // already showing
        }
        // Switch content
        switch (desired) {
            case SCATTER -> loadScatterChart();
            case DATATABLE -> loadDataTable();
            case BOX -> showPlaceholder("Box Plot view chưa được triển khai huhu");
            case REPORT -> showPlaceholder("Report view chưa được triển khai huhu");
            default -> contentArea.getChildren().clear();
        }
        currentView = desired;
    }

    private ViewType determineDesiredView() {
        if (scatterChart != null && scatterChart.isSelected()) return ViewType.SCATTER;
        if (dataTable != null && dataTable.isSelected()) return ViewType.DATATABLE;
        if (boxPlot != null && boxPlot.isSelected()) return ViewType.BOX;
        if (report != null && report.isSelected()) return ViewType.REPORT;
        return ViewType.NONE;
    }

    private void loadScatterChart() {
        try {
            Parent fxml = FXMLLoader.load(getClass().getResource("/pgt/cnv_view/FXML/MultiScatterChart.fxml"));
            contentArea.getChildren().setAll(fxml);
        } catch (IOException e) {
            showPlaceholder("Không thể load Scatter Chart: " + e.getMessage());
        }
    }

    private boolean canShowDataTable() {
        return !selectedSamples.isEmpty() && !selectedAlgorithms.isEmpty() && getPrimaryAlgorithmToken() != null;
    }

    private void loadDataTable() {
        if (!canShowDataTable()) { contentArea.getChildren().clear(); return; }
        String sample = selectedSamples.get(0).getText();
        String algoToken = getPrimaryAlgorithmToken();
        if (algoToken == null) { contentArea.getChildren().clear(); return; }
    Path binsFile = CnvData.resolveDataRoot()
        .resolve(sample)
        .resolve(algoToken)
        .resolve(CnvData.binsFileName(sample, algoToken));
        try {
            FXMLLoader loader = new FXMLLoader(getClass().getResource("/pgt/cnv_view/FXML/DataTable.fxml"));
            Parent root = loader.load();
            DataTableController ctrl = loader.getController();
            if (ctrl != null) ctrl.loadBinsFile(binsFile);
            contentArea.getChildren().setAll(root);
        } catch (IOException e) {
            showPlaceholder("Không thể load Data Table: " + e.getMessage());
        }
    }

    private void showPlaceholder(String msg) {
        javafx.scene.control.Label l = new javafx.scene.control.Label(msg);
        l.setStyle("-fx-padding:20; -fx-text-fill:#555; -fx-font-size:14px;");
        contentArea.getChildren().setAll(l);
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
    for (String sample : sampleNames) if (!CnvData.sampleHasAlgorithm(sample, algoToken)) return false; return true;
    }

    // Scan data root to preload existing samples dynamically
    private void loadExistingSamples() {
        try {
            Path dataRoot = CnvData.resolveDataRoot();
            if (!Files.exists(dataRoot) || !Files.isDirectory(dataRoot)) return;
            Files.list(dataRoot)
                    .filter(Files::isDirectory)
                    .map(p -> p.getFileName().toString())
                    .filter(CnvData::sampleDirectoryHasAnyAlgorithm)
                    .sorted()
                    .forEach(this::addSampleCheckbox);
        } catch (Exception ignored) {}
    }
    // Removed sampleDirectoryHasAnyAlgorithm & resolveDataRoot (now in CnvData)

    // Accessors for DataTable
    public List<String> getSelectedSampleNames() {
        return selectedSamples.stream().map(CheckBox::getText).toList();
    }

    // Return selected sample names in the visual order (order of checkboxes inside sampleContainer)
    public List<String> getSelectedSampleNamesInDisplayOrder() {
        List<String> ordered = new LinkedList<>();
        for (javafx.scene.Node n : sampleContainer.getChildren()) {
            if (n instanceof CheckBox cb && cb.isSelected()) {
                ordered.add(cb.getText());
            }
        }
        return ordered;
    }

    public String getPrimaryAlgorithmToken() { if (selectedAlgorithms.isEmpty()) return null; return CnvData.normalizeAlgorithm(selectedAlgorithms.get(0).getText()); }

    public List<String> getSelectedAlgorithmTokens() { List<String> tokens = new LinkedList<>(); for (CheckBox cb : selectedAlgorithms) tokens.add(CnvData.normalizeAlgorithm(cb.getText())); return tokens; }

    // Return selected algorithm tokens in fixed display order (baseline, bicseq2, wisecondorx, bluefuse)
    public List<String> getSelectedAlgorithmTokensInDisplayOrder() { List<String> ordered = new LinkedList<>(); CheckBox[] order = {baseline, bicSeq2, wisecondorX, blueFuse}; for (CheckBox cb : order) if (cb!=null && cb.isSelected()) ordered.add(CnvData.normalizeAlgorithm(cb.getText())); return ordered; }

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