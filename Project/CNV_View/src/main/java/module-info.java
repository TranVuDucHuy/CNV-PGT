module pgt.cnv_view {
    requires javafx.controls;
    requires javafx.fxml;
    requires javafx.web;

    requires org.controlsfx.controls;
    requires com.dlsc.formsfx;
    requires net.synedra.validatorfx;
    requires org.kordamp.ikonli.javafx;
    requires org.kordamp.bootstrapfx.core;
    requires eu.hansolo.tilesfx;
    requires com.almasb.fxgl.all;

// opens pgt.cnv_view to javafx.fxml;
// exports pgt.cnv_view;
    exports pgt.cnv_view.Application;
    opens pgt.cnv_view.Application to javafx.fxml;
    exports pgt.cnv_view.Controller;
    opens pgt.cnv_view.Controller to javafx.fxml;
}