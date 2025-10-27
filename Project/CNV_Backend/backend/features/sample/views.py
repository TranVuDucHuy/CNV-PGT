import uuid
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .service import SampleService


@csrf_exempt
@require_http_methods(["POST"])
def create_sample(request):
    """Create a new sample by uploading a BAM file."""
    patient_id = request.POST.get("patient_id")
    file = request.FILES.get("file")
    
    if not patient_id or not file:
        return JsonResponse({"error": "patient_id and file are required"}, status=400)

    try:
        patient_id = int(patient_id)
    except ValueError:
        return JsonResponse({"error": "patient_id must be an integer"}, status=400)

    sample = SampleService.add_sample(patient_id, file)
    return JsonResponse({
        "id": sample.id,
        "bam_url": sample.bam_url,
        "created_at": sample.created_at.isoformat(),
        "patient_id": sample.patient_id,
    }, status=201)


@csrf_exempt
@require_http_methods(["GET"])
def read_sample(request, sample_id: str):
    """Get a specific sample by ID."""
    sample = SampleService.get_sample(sample_id)
    if not sample:
        return JsonResponse({"error": "not found"}, status=404)
    
    return JsonResponse({
        "id": sample.id,
        "bam_url": sample.bam_url,
        "created_at": sample.created_at.isoformat(),
        "patient_id": sample.patient_id,
    })


@csrf_exempt
@require_http_methods(["GET"])
def list_samples(request):
    """List all samples."""
    samples = SampleService.get_all_samples()
    return JsonResponse([{
        "id": sample.id,
        "bam_url": sample.bam_url,
        "created_at": sample.created_at.isoformat(),
        "patient_id": sample.patient_id,
    } for sample in samples], safe=False)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_sample(request, sample_id: str):
    """Delete a sample by ID."""
    ok = SampleService.remove_sample(sample_id)
    if not ok:
        return JsonResponse({"error": "not found"}, status=404)
    
    return JsonResponse({"status": "deleted"})


@csrf_exempt
@require_http_methods(["GET"])
def download_sample_file(request, sample_id: str):
    """Download the BAM file for a sample."""
    file_stream = SampleService.get_sample_file(sample_id)
    if not file_stream:
        return JsonResponse({"error": "not found"}, status=404)

    file_stream.seek(0)
    response = HttpResponse(file_stream.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="sample_{sample_id}.bam"'
    return response

