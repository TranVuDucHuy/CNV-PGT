package pgt.cnv_view.feature.sample;

import okhttp3.MediaType;
import okhttp3.RequestBody;
import pgt.cnv_view.util.ApiClient;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.List;

public class SampleServiceImpl implements SampleService {
    private final RetrofitSampleService service = ApiClient.createService(RetrofitSampleService.class);

    @Override
    public Sample uploadSampleFile(Long patientId, File bamFile) throws IOException {
        RequestBody patientIdBody = RequestBody
                .create(patientId.toString(), MediaType.parse("text/plain"));

        RequestBody fileBody = RequestBody
                .create(bamFile, MediaType.parse("application/octet-stream"));

        var filePart = okhttp3.MultipartBody.Part
                .createFormData("file", bamFile.getName(), fileBody);

        var call = service.postSampleFile(patientIdBody, filePart);
        return call.execute().body();
    }

    @Override
    public void deleteSample(Long sampleId) throws IOException {
        service.deleteSample(sampleId).execute();
    }

    @Override
    public Sample getSample(Long sampleId) throws IOException {
        return service.getSample(sampleId).execute().body();
    }

    @Override
    public List<Sample> getAllSamples() throws IOException {
        return service.getAllSamples().execute().body();
    }

    @Override
    public File downloadSampleFile(Long sampleId) throws Exception {
        var response = service.downloadSampleFile(sampleId).execute();

        var responseBody = response.body();

        if (!response.isSuccessful() || responseBody == null) {
            throw new IOException("Failed to download file: " + response.message());
        }

        // Save the file to a temporary location
        File tempFile = File.createTempFile("sample_" + sampleId, ".bam");

        var outputStream = Files.newOutputStream(tempFile.toPath());
        responseBody.byteStream().transferTo(outputStream);

        responseBody.close();
        return tempFile;
    }
}
