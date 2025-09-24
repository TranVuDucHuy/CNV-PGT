package pgt.cnv_view.feature.sample;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class Sample {
    private Long id;
    private String bamUrl;
    private String createdAt;
    private Long patientId;
}
