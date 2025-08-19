package pgt.cnv_view.Controller;

import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.fxml.Initializable;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.CheckBox;
import javafx.scene.layout.StackPane;
import javafx.stage.Stage;


import java.io.IOException;
import java.net.URL;
import java.util.ResourceBundle;
import java.util.LinkedList;
import java.util.List;

import javafx.event.ActionEvent;

public class ViewController implements Initializable {
    @FXML
    private StackPane contentArea;

    @FXML
    private CheckBox sample1, sample2, sample3;

    // Store up to 2 selected sample checkboxes (FIFO behavior)
    private final List<CheckBox> selectedSamples = new LinkedList<>();

    @FXML
    private CheckBox baseline, bicSeq2, wisecondorX, blueFuse, scatterChart, boxPlot, dataTable, report;

    // Track up to 2 selected algorithm checkboxes (FIFO behavior)
    private final List<CheckBox> selectedAlgorithms = new LinkedList<>();

    @Override
    public void initialize(URL location, ResourceBundle resources) {
        disableCheckBoxes(true);

    setupSampleSelection(sample1);
    setupSampleSelection(sample2);
    setupSampleSelection(sample3);

        addSelectionListeners();
    addViewGroupMutualExclusion();
    }

    public void scatterChart(ActionEvent actionEvent) throws IOException {
        Parent fxml = FXMLLoader.load(getClass().getResource("/pgt/cnv_view/FXML/ScatterChart.fxml"));
        contentArea.getChildren().removeAll();
        contentArea.getChildren().setAll(fxml);
    }

    public void dataTable(ActionEvent actionEvent) throws IOException {
        Parent fxml = FXMLLoader.load(getClass().getResource("/pgt/cnv_view/FXML/DataTable.fxml"));
        contentArea.getChildren().removeAll();
        contentArea.getChildren().setAll(fxml);
    }

    public void addSample(ActionEvent actionEvent) throws IOException {
        Parent fxml = FXMLLoader.load(getClass().getResource("/pgt/cnv_view/FXML/AddSample.fxml"));

        Scene scene = new Scene(fxml);
        Stage primaryStage = new Stage();
        primaryStage.setTitle("Add Sample");
        primaryStage.setScene(scene);
        primaryStage.initModality(javafx.stage.Modality.APPLICATION_MODAL);
        primaryStage.initOwner(contentArea.getScene().getWindow());
        primaryStage.show();
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
}