package pgt.cnv_view.application;

import javafx.application.Application;
import javafx.fxml.FXMLLoader;
import javafx.scene.Scene;
import javafx.stage.Stage;

import java.io.IOException;

public class ViewApplication extends Application {
    @Override
    public void start(Stage stage) throws IOException {
        FXMLLoader fxmlLoader = new FXMLLoader(ViewApplication.class.getResource("/pgt/cnv_view/FXML/Dashboard.fxml"));
        Scene scene = new Scene(fxmlLoader.load(), 1280, 720);

        stage.setTitle("CNV View");
        stage.setResizable(true);
        stage.setScene(scene);
        stage.show();

        String css = getClass().getResource("/pgt/cnv_view/CSS/Sample.css").toExternalForm();
        scene.getStylesheets().add(css);
    }

    public static void main(String[] args) {
        launch();
    }
}