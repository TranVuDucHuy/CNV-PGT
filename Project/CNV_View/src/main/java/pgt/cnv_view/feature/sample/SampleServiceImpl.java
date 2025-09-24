package pgt.cnv_view.feature.sample;

import okhttp3.MediaType;
import okhttp3.RequestBody;
import pgt.cnv_view.util.ApiClient;

import java.io.File;
import java.io.IOException;
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
}
