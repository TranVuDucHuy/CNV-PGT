import uuid
from django.db import models
from django.utils import timezone


def generate_sample_id():
    """Generate a unique ID for a sample."""
    return uuid.uuid4().hex


class Sample(models.Model):
    id = models.CharField(max_length=128, primary_key=True, default=generate_sample_id, editable=False)
    
    bam_url = models.CharField(max_length=512)
    created_at = models.DateTimeField(default=timezone.now)
    patient_id = models.IntegerField(db_index=True)

    class Meta:
        db_table = "samples"
        ordering = ['-created_at']

    def __str__(self):
        return f"Sample {self.id}"

