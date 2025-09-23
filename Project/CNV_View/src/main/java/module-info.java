module pgt.cnv_view {
    requires javafx.controls;
    requires javafx.fxml;
    requires javafx.web;
    requires transitive javafx.base;

    requires org.controlsfx.controls;
    requires com.dlsc.formsfx;
    requires net.synedra.validatorfx;
    requires org.kordamp.ikonli.javafx;
    requires org.kordamp.bootstrapfx.core;
    requires eu.hansolo.tilesfx;
    requires com.almasb.fxgl.all;
    requires java.logging;
    requires okhttp3;

// opens pgt.cnv_view to javafx.fxml;
// exports pgt.cnv_view;
    exports pgt.cnv_view.application;
    opens pgt.cnv_view.application to javafx.fxml;
    exports pgt.cnv_view.controller;
    opens pgt.cnv_view.controller to javafx.fxml;
}