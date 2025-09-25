package pgt.cnv_view;


import org.junit.jupiter.api.Test;
import pgt.cnv_view.feature.sample.SampleService;
import pgt.cnv_view.feature.sample.SampleServiceImpl;

import java.io.File;

public class SampleServiceTest {
    private final SampleService service = new SampleServiceImpl();
    private final Long patientId = 1L;

    @Test
    void testPost() throws Exception {
        var s = service.uploadSampleFile(
                patientId,
                new File("pom.xml")
        );
        System.out.println(s);
        assert s != null;
    }

    @Test
    void testGetAll() throws Exception {
        var samples = service.getAllSamples();
        System.out.println(samples);
        assert samples != null;
    }

    @Test
    void testGet() throws Exception {
        var s = service.getSample(1L);
        System.out.println(s);
        assert s != null;
    }

    @Test
    void testDownload() throws Exception {
        var f = service.downloadSampleFile(1L);
        System.out.println(f);
        assert f != null;
    }

    @Test
    void testDelete() throws Exception {
        service.deleteSample(2L);
    }

}
