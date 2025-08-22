package pgt.cnv_view.Controller;

import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.control.TableColumn;
import javafx.scene.control.TableView;
import javafx.scene.control.cell.PropertyValueFactory;
import javafx.scene.control.Alert;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;

import java.net.URL;
import java.nio.file.*;
import java.io.IOException;
import java.util.ResourceBundle;
import java.util.stream.Stream;

public class DataTableController implements Initializable {
	@FXML private javafx.scene.layout.BorderPane root;

	@FXML private TableView<BinRow> table;
	@FXML private TableColumn<BinRow, String> colChrom;
	@FXML private TableColumn<BinRow, Long> colStart;
	@FXML private TableColumn<BinRow, Long> colEnd;
	@FXML private TableColumn<BinRow, Double> colCopy;
	@FXML private TableColumn<BinRow, String> colType;

	@Override
	public void initialize(URL location, ResourceBundle resources) {
		if (table != null) {
			colChrom.setCellValueFactory(new PropertyValueFactory<>("chromosome"));
			colStart.setCellValueFactory(new PropertyValueFactory<>("start"));
			colEnd.setCellValueFactory(new PropertyValueFactory<>("end"));
			colCopy.setCellValueFactory(new PropertyValueFactory<>("copyNumber"));
			colType.setCellValueFactory(new PropertyValueFactory<>("type"));
		}
	}

	// Public API: load a bins.tsv file given its path
	public void loadBinsFile(Path binsFile) {
		if (binsFile == null) return;
		if (!Files.exists(binsFile)) {
			Alert a = new Alert(Alert.AlertType.WARNING, "File not found: " + binsFile.getFileName());
			a.showAndWait();
			return;
		}
		try {
			ObservableList<BinRow> rows = FXCollections.observableArrayList();
			try (Stream<String> lines = Files.lines(binsFile)) {
				lines.filter(l -> !l.isBlank() && !l.startsWith("#"))
						.forEach(line -> {
							String[] parts = line.split("\t");
							// Accept either 4-column (Chromosome,Start,End,CopyNumber) or 5-column (+Type)
							if (parts.length >= 4) {
								try {
									String chr = parts[0];
									long start = Long.parseLong(parts[1]);
									long end = Long.parseLong(parts[2]);
									String copyStr = parts[3];
									double copy = copyStr.equalsIgnoreCase("nan") ? Double.NaN : Double.parseDouble(copyStr);
									String type = parts.length >= 5 ? parts[4] : "";
									rows.add(new BinRow(chr, start, end, copy, type));
								} catch (NumberFormatException ignored) {}
							}
						});
			}
			table.setItems(rows);
			if (rows.isEmpty()) {
				table.setPlaceholder(new javafx.scene.control.Label("No rows parsed (check column count)"));
			}
		} catch (IOException e) {
			Alert a = new Alert(Alert.AlertType.ERROR, "Cannot load bins file: " + e.getMessage());
			a.showAndWait();
		}
	}

	public static class BinRow {
		private final String chromosome;
		private final long start;
		private final long end;
		private final double copyNumber;
		private final String type;
		public BinRow(String chromosome, long start, long end, double copyNumber, String type) {
			this.chromosome = chromosome; this.start = start; this.end = end; this.copyNumber = copyNumber; this.type = type;
		}
		public String getChromosome() { return chromosome; }
		public long getStart() { return start; }
		public long getEnd() { return end; }
		public double getCopyNumber() { return copyNumber; }
		public String getType() { return type; }
	}
}
