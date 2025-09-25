from flask import request, jsonify

from . import sample_bp
from .service import SampleService


@sample_bp.post("/samples")
def create_sample():
    patient_id = request.form.get("patient_id", type=int)
    file = request.files.get("file")
    if not patient_id or not file:
        return jsonify({"error": "patient_id and file are required"}), 400

    sample = SampleService.add_sample(patient_id, file)
    return (
        jsonify({
            "id": sample.id,
            "bam_url": sample.bam_url,
            "created_at": sample.created_at.isoformat(),
            "patient_id": sample.patient_id,
        }),
        201,
    )


@sample_bp.get("/samples/<int:sample_id>")
def read_sample(sample_id: int):
    sample = SampleService.get_sample(sample_id)
    if not sample:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "id": sample.id,
        "bam_url": sample.bam_url,
        "created_at": sample.created_at.isoformat(),
        "patient_id": sample.patient_id,
    })
        

@sample_bp.get("/samples")
def list_samples():
    samples = SampleService.get_all_samples()
    return jsonify([{
        "id": sample.id,
        "bam_url": sample.bam_url,
        "created_at": sample.created_at.isoformat(),
        "patient_id": sample.patient_id,
    } for sample in samples]), 200


@sample_bp.delete("/samples/<int:sample_id>")
def delete_sample(sample_id: int):
    ok = SampleService.remove_sample(sample_id)
    if not ok:
        return jsonify({"error": "not found"}), 404
    return jsonify({"status": "deleted"})


@sample_bp.get("/samples/<int:sample_id>/file")
def download_sample_file(sample_id: int):
    file_stream = SampleService.get_sample_file(sample_id)
    if not file_stream:
        return jsonify({"error": "not found"}), 404

    file_stream.seek(0)
    return (
        file_stream.read(),
        200,
        {
            "Content-Type": "application/octet-stream",
            "Content-Disposition": f'attachment; filename="sample_{sample_id}.bam"',
        },
    )


