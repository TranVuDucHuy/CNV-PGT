package pgt.cnv_view.Controller;

import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.control.MenuButton;
import javafx.scene.control.MenuItem;

import java.net.URL;
import java.util.ResourceBundle;

public class AddSample implements Initializable {

	@FXML
	private MenuButton algorithmMenu; // MenuButton hiển thị algorithm đã chọn

	private String selectedAlgorithm; // Lưu tên algorithm đã chọn

	@Override
	public void initialize(URL location, ResourceBundle resources) {
		// Có thể đặt text mặc định/prompt nếu cần
		if (algorithmMenu != null) {
			algorithmMenu.setText("Algorithm");
		}
	}

	@FXML
	private void onAlgorithmSelect(ActionEvent event) {
		Object src = event.getSource();
		if (src instanceof MenuItem item) {
			selectedAlgorithm = item.getText();
			if (algorithmMenu != null) {
				algorithmMenu.setText(selectedAlgorithm); // cập nhật tiêu đề
			}
		}
	}

	public String getSelectedAlgorithm() {
		return selectedAlgorithm;
	}
}
