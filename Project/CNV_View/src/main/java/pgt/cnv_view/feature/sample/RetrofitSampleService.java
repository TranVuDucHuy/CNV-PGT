package pgt.cnv_view.feature.sample;

import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import retrofit2.Call;
import retrofit2.http.*;

import java.util.List;

public interface RetrofitSampleService {
    @Multipart
    @POST("/api/samples")
    Call<Sample> postSampleFile(
            @Part("patient_id") RequestBody patientId,
            @Part MultipartBody.Part bamFile
    );

    @DELETE("/api/samples/{sample_id}")
    Call<Void> deleteSample(@Path("sample_id") Long sampleId);

    @GET("/api/samples/{sample_id}")
    Call<Sample> getSample(@Path("sample_id") Long sampleId);

    @GET("/api/samples")
    Call<List<Sample>> getAllSamples();
}
