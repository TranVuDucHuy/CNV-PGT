package pgt.cnv_view.feature.sample;

import java.io.File;
import java.util.List;

public interface SampleService {
    Sample uploadSampleFile(Long patientId, File bamFile) throws Exception;
    void deleteSample(Long sampleId) throws Exception;
    Sample getSample(Long sampleId) throws Exception;
    List<Sample> getAllSamples() throws Exception;
    File downloadSampleFile(Long sampleId) throws Exception;
}
