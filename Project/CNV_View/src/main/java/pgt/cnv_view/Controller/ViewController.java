package pgt.cnv_view.Controller;

import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.fxml.Initializable;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.CheckBox;
import javafx.scene.control.Label;
import javafx.scene.input.MouseEvent;
import javafx.scene.layout.StackPane;
import javafx.stage.Stage;


import java.io.IOException;
import java.net.URL;
import java.util.ResourceBundle;

import javafx.event.ActionEvent;

public class ViewController implements Initializable {
    @FXML
    private StackPane contentArea;

    @FXML
    private Label sample1, sample2, sample3;

    private Label selectedLabel;

    @FXML
    private CheckBox baseline, bicSeq2, wisecondorX, blueFuse, scatterChart, boxPlot, dataTable, report;

    @Override
    public void initialize(URL location, ResourceBundle resources) {
        disableCheckBoxes(true);

        setupLabelSelection(sample1);
        setupLabelSelection(sample2);
        setupLabelSelection(sample3);

        addSelectionListeners();
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

    private void setupLabelSelection(Label label) {
        label.setOnMouseClicked(event -> {
            if (selectedLabel != null) {
                selectedLabel.getStyleClass().remove("selected");
            }
            label.getStyleClass().add("selected");
            selectedLabel = label;

            resetCheckBoxes();
            disableCheckBoxes(false);
            checkFirstGroupSelection();
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
        baseline.selectedProperty().addListener((observable, oldValue, newValue) -> checkFirstGroupSelection());
        bicSeq2.selectedProperty().addListener((observable, oldValue, newValue) -> checkFirstGroupSelection());
        wisecondorX.selectedProperty().addListener((observable, oldValue, newValue) -> checkFirstGroupSelection());
        blueFuse.selectedProperty().addListener((observable, oldValue, newValue) -> checkFirstGroupSelection());
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
}