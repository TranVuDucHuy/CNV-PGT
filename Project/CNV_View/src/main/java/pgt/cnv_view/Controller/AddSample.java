package pgt.cnv_view.Controller;

import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.control.*;
import javafx.stage.FileChooser;
import javafx.stage.Window;

import java.net.URL;
import java.util.ResourceBundle;
import java.nio.file.*;
import java.io.IOException;

public class AddSample implements Initializable {

	@FXML
	private MenuButton algorithmMenu; // MenuButton hiển thị algorithm đã chọn
	@FXML
	private TextField binFilePathField;
	@FXML
	private TextField segmentFilePathField;

	private String selectedAlgorithm; // Lưu tên algorithm đã chọn
	private java.io.File lastDirectory; // nhớ thư mục lần cuối
	private ViewController parentController; // callback parent

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

	@FXML
	private void browseBinFile(ActionEvent event) {
		java.io.File file = showFileChooser("Chọn Bin File");
		if (file != null && binFilePathField != null) {
			binFilePathField.setText(file.getAbsolutePath());
		}
	}

	@FXML
	private void browseSegmentFile(ActionEvent event) {
		java.io.File file = showFileChooser("Chọn Segment File");
		if (file != null && segmentFilePathField != null) {
			segmentFilePathField.setText(file.getAbsolutePath());
		}
	}

	private java.io.File showFileChooser(String title) {
		FileChooser chooser = new FileChooser();
		chooser.setTitle(title);
		if (lastDirectory != null && lastDirectory.exists()) {
			chooser.setInitialDirectory(lastDirectory);
		}
		chooser.getExtensionFilters().addAll(
				new FileChooser.ExtensionFilter("TSV Files", "*.tsv"),
				new FileChooser.ExtensionFilter("All Files", "*.*")
		);
		Window window = algorithmMenu != null ? algorithmMenu.getScene().getWindow() : null;
		java.io.File file = chooser.showOpenDialog(window);
		if (file != null) {
			lastDirectory = file.getParentFile();
		}
		return file;
	}

	public String getSelectedAlgorithm() {
		return selectedAlgorithm;
	}

	public void setParentController(ViewController parentController) {
		this.parentController = parentController;
	}

	@FXML
	private void onAdd(ActionEvent event) {
		// Basic presence checks
		if (selectedAlgorithm == null || selectedAlgorithm.isBlank()) {
			showAlert(Alert.AlertType.WARNING, "Missing Algorithm", "Please choose an algorithm.");
			return;
		}
		String binPath = binFilePathField != null ? binFilePathField.getText() : null;
		String segmentPath = segmentFilePathField != null ? segmentFilePathField.getText() : null;
		if (isBlank(binPath) || isBlank(segmentPath)) {
			showAlert(Alert.AlertType.WARNING, "Missing File", "Please choose both Bin File and Segment File.");
			return;
		}

		java.io.File binFile = new java.io.File(binPath);
		java.io.File segmentFile = new java.io.File(segmentPath);

		// enforce .tsv extension
		if (!binFile.getName().toLowerCase().endsWith(".tsv") || !segmentFile.getName().toLowerCase().endsWith(".tsv")) {
			showAlert(Alert.AlertType.ERROR, "Wrong extension", "Both files must have .tsv extension");
			return;
		}

		String algoToken = normalizeAlgorithm(selectedAlgorithm);
		String binBase = stripExtension(binFile.getName());
		String segBase = stripExtension(segmentFile.getName());

		ValidationResult vr = validatePatterns(binBase, segBase, algoToken);
		if (!vr.valid) {
			showAlert(Alert.AlertType.ERROR, "Wrong file's name", vr.message);
			return;
		}

		try {
			// Determine target paths and check if already added BEFORE copying
			Path dataRoot = resolveWritableDataRoot();
			Path targetDir = dataRoot.resolve(vr.sampleName).resolve(algoToken);
			Path existingBin = targetDir.resolve(vr.sampleName + "_" + algoToken + "_bins.tsv");
			Path existingSeg = targetDir.resolve(vr.sampleName + "_" + algoToken + "_segments.tsv");
			if (Files.exists(existingBin) && Files.exists(existingSeg)) {
				showAlert(Alert.AlertType.INFORMATION, "Already exists", "Sample '" + vr.sampleName + "' with algorithm '" + selectedAlgorithm + "' already exists.");
				if (parentController != null) parentController.registerSample(vr.sampleName);
				closeWindow();
				return;
			}
			// Copy now
			Path copiedBin = copyIntoDataFolder(binFile.toPath(), vr.sampleName, algoToken, true);
			Path copiedSeg = copyIntoDataFolder(segmentFile.toPath(), vr.sampleName, algoToken, false);
			showAlert(Alert.AlertType.INFORMATION, "Success", "Added sample '" + vr.sampleName + "' with algorithm '" + selectedAlgorithm + "' (\n" + copiedBin.getFileName() + "\n" + copiedSeg.getFileName() + ")");
			if (parentController != null) parentController.registerSample(vr.sampleName);
			closeWindow();
		} catch (IOException ioe) {
			showAlert(Alert.AlertType.ERROR, "Copy error", "Cannot copy files into Data folder: " + ioe.getMessage());
		}
	}

	private record ValidationResult(boolean valid, String message, String sampleName) {}

	private ValidationResult validatePatterns(String binBase, String segBase, String algoToken) {
		if (!binBase.endsWith("_bins")) {
			return new ValidationResult(false, "Bin file must end with _bins", null);
		}
		if (!segBase.endsWith("_segments")) {
			return new ValidationResult(false, "Segment file must end with _segments", null);
		}
		String binNoSuffix = binBase.substring(0, binBase.length() - 5); // remove _bins
		String segNoSuffix = segBase.substring(0, segBase.length() - 9); // remove _segments
		String algoPattern = "_" + algoToken;
		if (!binNoSuffix.endsWith(algoPattern)) {
			return new ValidationResult(false, "Bin file name must be in the format sample_" + algoToken + "_bins", null);
		}
		if (!segNoSuffix.endsWith(algoPattern)) {
			return new ValidationResult(false, "Segment file name must be in the format sample_" + algoToken + "_segments", null);
		}
		String sampleBin = binNoSuffix.substring(0, binNoSuffix.length() - algoPattern.length());
		String sampleSeg = segNoSuffix.substring(0, segNoSuffix.length() - algoPattern.length());
		if (sampleBin.isBlank() || sampleSeg.isBlank()) {
			return new ValidationResult(false, "Sample part must not be empty", null);
		}
		if (!sampleBin.equals(sampleSeg)) {
			return new ValidationResult(false, "Sample names between the two files must match", null);
		}
		return new ValidationResult(true, "", sampleBin);
	}

	private String normalizeAlgorithm(String algorithm) {
		// Chuyển sang lowercase, bỏ khoảng trắng
		return algorithm.toLowerCase().replaceAll("\\s+", "");
	}

	private String stripExtension(String filename) {
		int idx = filename.lastIndexOf('.');
		return idx > 0 ? filename.substring(0, idx) : filename;
	}

	private boolean isBlank(String s) { return s == null || s.trim().isEmpty(); }

	private void showAlert(Alert.AlertType type, String title, String content) {
		Alert alert = new Alert(type);
		alert.setTitle(title);
		alert.setHeaderText(null);
		alert.setContentText(content);
		alert.showAndWait();
	}

	private void closeWindow() {
		// Dùng một control bất kỳ để lấy Stage hiện tại
		Window w = null;
		if (algorithmMenu != null) w = algorithmMenu.getScene().getWindow();
		else if (binFilePathField != null) w = binFilePathField.getScene().getWindow();
		if (w instanceof javafx.stage.Stage stage) {
			stage.close();
		}
	}

	private Path copyIntoDataFolder(Path source, String sampleName, String algoToken, boolean isBin) throws IOException {
		Path dataRoot = resolveWritableDataRoot();
		Path targetDir = dataRoot.resolve(sampleName).resolve(algoToken);
		Files.createDirectories(targetDir);
		String targetFileName = sampleName + "_" + algoToken + (isBin ? "_bins.tsv" : "_segments.tsv");
		Path target = targetDir.resolve(targetFileName);
		Files.copy(source, target, StandardCopyOption.REPLACE_EXISTING);
		return target;
	}

	private Path resolveWritableDataRoot() throws IOException {
		Path projectData = Paths.get("src", "main", "resources", "pgt", "cnv_view", "Data");
		if (Files.exists(projectData) && Files.isDirectory(projectData) && Files.isWritable(projectData)) {
			return projectData;
		}
		Path external = Paths.get(System.getProperty("user.dir"), "data");
		Files.createDirectories(external);
		return external;
	}
}
