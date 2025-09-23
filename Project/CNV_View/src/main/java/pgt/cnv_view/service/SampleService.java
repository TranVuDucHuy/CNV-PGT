package pgt.cnv_view.service;


import okhttp3.*;
import pgt.cnv_view.util.Api;

import java.io.File;
import java.io.IOException;

public class SampleService {
    private static final String ENDPOINT = "/samples";

    Api api = Api.Holder.INSTANCE;

    public void postSampleFile(File file, String patientId) throws IOException {
        RequestBody textBody = RequestBody.create(patientId, MediaType.parse("text/plain"));
        RequestBody fileBody = RequestBody.create(file, MediaType.parse("application/octet-stream"));

        // Build multipart request
        MultipartBody requestBody = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("textField", null, textBody)
                .addFormDataPart("file", file.getName(), fileBody)
                .build();

        

        try (Response response = api.post(ENDPOINT, requestBody)) {
            System.out.println("Response code: " + response.code());
            assert response.body() != null;
            System.out.println("Body: " + response.body().string());
        }
    }

    public void deleteSample(String sampleId) throws IOException {
        String endpoint = ENDPOINT + "/" + sampleId;
        try (Response response = api.delete(endpoint)) {
            System.out.println("Response code: " + response.code());
            assert response.body() != null;
            System.out.println("Body: " + response.body().string());
        }
    }

    public void getSample(String sampleId) throws IOException {
        String endpoint = ENDPOINT + "/" + sampleId;
        try (Response response = api.get(endpoint)) {
            System.out.println("Response code: " + response.code());
            assert response.body() != null;
            System.out.println("Body: " + response.body().string());
        }
    }
}
