package pgt.cnv_view.Controller;

import javafx.application.Platform;
import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.control.Label;
import javafx.scene.control.TableColumn;
import javafx.scene.control.TableView;
import javafx.scene.control.TitledPane;
import javafx.scene.control.cell.PropertyValueFactory;
import javafx.scene.layout.VBox;
import pgt.cnv_view.util.CnvData;

import java.io.IOException;
import java.net.URL;
import java.nio.file.*;
import java.util.*;
import java.util.stream.Stream;

/**
 * Report: one table per (sample, algorithm) showing only segments with type != no_change.
 */
public class ReportController implements Initializable {
    @FXML private VBox reportRoot; // container for dynamic tables

    @Override public void initialize(URL location, ResourceBundle resources) { Platform.runLater(this::refresh); }

    public void refresh() {
        if (reportRoot == null) return;
        reportRoot.getChildren().clear();
        ViewController vc = ViewControllerStaticRef.get();
        if (vc == null) { reportRoot.getChildren().add(new Label("No context")); return; }
        List<String> samples = vc.getSelectedSampleNamesInDisplayOrder();
        List<String> algos = vc.getSelectedAlgorithmTokensInDisplayOrder();
        if (samples.isEmpty() || algos.isEmpty()) { reportRoot.getChildren().add(new Label("Chưa chọn sample / algorithm")); return; }
        if (samples.size() >= 2 && algos.size() > 1) algos = List.of(algos.get(0)); // enforce first algo only with multi-sample
        // Simply list tables per (sample, algorithm) in the original selection order (no cycle headers)
        for (String sample : samples) {
            for (String algo : algos) {
                Path seg = CnvData.resolveDataRoot().resolve(sample).resolve(algo).resolve(CnvData.segmentsFileName(sample, algo));
                if (!Files.exists(seg)) continue;
                TableView<SegmentRow> tv = buildTable();
                loadSegments(seg, tv);
                String title = CnvData.displaySampleName(sample) + " -- " + CnvData.prettyAlgorithm(algo);
                TitledPane tp = new TitledPane(title, tv);
                tp.setExpanded(true);
                reportRoot.getChildren().add(tp);
            }
        }
        if (reportRoot.getChildren().isEmpty()) reportRoot.getChildren().add(new Label("Không có segment khác 'no_change'"));
    }

    private TableView<SegmentRow> buildTable() {
        TableView<SegmentRow> tv = new TableView<>();
        tv.setPrefHeight(220);
    TableColumn<SegmentRow,String> chr = new TableColumn<>("Chromosome"); chr.setCellValueFactory(new PropertyValueFactory<>("chromosome"));
    TableColumn<SegmentRow,Long> start = new TableColumn<>("Start"); start.setCellValueFactory(new PropertyValueFactory<>("start"));
    TableColumn<SegmentRow,Long> end = new TableColumn<>("End"); end.setCellValueFactory(new PropertyValueFactory<>("end"));
    TableColumn<SegmentRow,Double> copy = new TableColumn<>("Copy number"); copy.setCellValueFactory(new PropertyValueFactory<>("copyNumber"));
    TableColumn<SegmentRow,String> typeCol = new TableColumn<>("Type"); typeCol.setCellValueFactory(new PropertyValueFactory<>("type"));
    TableColumn<SegmentRow,String> mosaic = new TableColumn<>("Mosaic %"); mosaic.setCellValueFactory(new PropertyValueFactory<>("mosaic"));
    tv.getColumns().add(chr);
    tv.getColumns().add(start);
    tv.getColumns().add(end);
    tv.getColumns().add(copy);
    tv.getColumns().add(typeCol);
    tv.getColumns().add(mosaic);
        return tv;
    }

    private void loadSegments(Path segFile, TableView<SegmentRow> table) {
        try (Stream<String> lines = Files.lines(segFile)) {
            lines.skip(1).filter(l -> !l.isBlank()).map(l -> l.split("\t"))
                    .filter(p -> p.length >= 5) // need at least through Type
                    .forEach(p -> {
                        try {
                            String chr = p[0];
                            long start = Long.parseLong(p[1]);
                            long end = Long.parseLong(p[2]);
                            double copy = Double.parseDouble(p[3]);
                            String rawType = p[4];
                            String norm = norm(rawType);
                            if (!norm.equals("no_change")) {
                                String mosaic = p.length > 5 ? p[5].trim() : "";
                                if (mosaic.equalsIgnoreCase("nan")) mosaic = ""; // hide nan
                                // keep special words like aneuploidy, else ensure % sign if numeric without it? (assume already formatted)
                                table.getItems().add(new SegmentRow(chr, start, end, copy, capitalize(norm), mosaic));
                            }
                        } catch (NumberFormatException ignored) { /* skip malformed line */ }
                    });
        } catch (IOException e) { table.setPlaceholder(new Label("Lỗi: " + e.getMessage())); }
        if (table.getItems().isEmpty()) table.setPlaceholder(new Label("Không có segment"));
    }

    private String norm(String raw) { if (raw==null) return "no_change"; String t = raw.trim().toLowerCase(Locale.ROOT); if (t.equals("loss")||t.equals("del")||t.equals("deletion")||t.equals("loh")) return "loss"; if (t.equals("gain")||t.equals("dup")||t.equals("duplication")||t.equals("amp")||t.equals("amplification")) return "gain"; return "no_change"; }

    private String capitalize(String t) { if (t==null||t.isEmpty()) return t; return Character.toUpperCase(t.charAt(0))+t.substring(1); }

    public static class SegmentRow { private final String chromosome; private final long start; private final long end; private final double copyNumber; private final String type; private final String mosaic; public SegmentRow(String chromosome,long start,long end,double copyNumber,String type,String mosaic){this.chromosome=chromosome;this.start=start;this.end=end;this.copyNumber=copyNumber;this.type=type;this.mosaic=mosaic;} public String getChromosome(){return chromosome;} public long getStart(){return start;} public long getEnd(){return end;} public double getCopyNumber(){return copyNumber;} public String getType(){return type;} public String getMosaic(){return mosaic;} }
}
