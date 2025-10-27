from django.contrib import admin
from .models import Sample


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient_id', 'created_at', 'bam_url')
    list_filter = ('created_at', 'patient_id')
    search_fields = ('id', 'patient_id')
    readonly_fields = ('created_at',)

