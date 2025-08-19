package pgt.cnv_view.Controller;

import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.control.MenuButton;
import javafx.scene.control.MenuItem;

import java.net.URL;
import java.util.ResourceBundle;

public class ScatterChart implements Initializable {

	@FXML
	private MenuButton dataMenu;
	@FXML
	private MenuButton chromosomeMenu;

	@Override
	public void initialize(URL location, ResourceBundle resources) {
		// Set default display text if needed
		if (dataMenu != null) dataMenu.setText("Data");
		if (chromosomeMenu != null) chromosomeMenu.setText("Chromosome");
	}

	@FXML
	private void onDataSelect(ActionEvent event) {
		if (event.getSource() instanceof MenuItem item && dataMenu != null) {
			dataMenu.setText(item.getText());
		}
	}

	@FXML
	private void onChromosomeSelect(ActionEvent event) {
		if (event.getSource() instanceof MenuItem item && chromosomeMenu != null) {
			chromosomeMenu.setText(item.getText());
		}
	}
}
