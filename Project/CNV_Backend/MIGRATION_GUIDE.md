# Flask to Django Migration Guide

This guide explains the changes made during the migration from Flask to Django.

## Summary of Changes

### 1. Dependencies (requirements.txt)

- **Removed**: Flask, Flask-Cors, Flask-SQLAlchemy, Flask-Migrate, SQLAlchemy
- **Added**: Django, django-cors-headers, mysqlclient (for MySQL support)

### 2. Project Structure

**Before (Flask)**:

```
app/
  __init__.py          # Flask app factory
  config.py            # Configuration
  extensions.py        # SQLAlchemy, Migrate
  features/
    sample/
      models.py        # SQLAlchemy models
      routes.py        # Flask routes
      service.py       # Business logic
```

**After (Django)**:

```
backend/               # Django project root
  settings.py          # Django settings
  urls.py             # Main URL configuration
  wsgi.py, asgi.py    # Application servers
  features/            # Django apps
    sample/
      models.py        # Django models
      views.py         # Django views
      urls.py         # URL routing
      service.py      # Business logic
      admin.py        # Admin interface
      apps.py         # App configuration
manage.py             # Django management script
```

### 3. Models Conversion

#### Flask/SQLAlchemy:

```python
from app.extensions import db

class Sample(db.Model):
    __tablename__ = "samples"

    id = db.Column(db.String(128), primary_key=True)
    bam_url = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    patient_id = db.Column(db.Integer, nullable=False, index=True)
```

#### Django:

```python
from django.db import models
import uuid

def generate_sample_id():
    return uuid.uuid4().hex

class Sample(models.Model):
    id = models.CharField(max_length=128, primary_key=True,
                         default=generate_sample_id, editable=False)
    bam_url = models.CharField(max_length=512)
    created_at = models.DateTimeField(default=timezone.now)
    patient_id = models.IntegerField(db_index=True)

    class Meta:
        db_table = "samples"
        ordering = ['-created_at']
```

### 4. Views/Routes Conversion

#### Flask:

```python
from flask import request, jsonify
from . import sample_bp

@sample_bp.post("/samples")
def create_sample():
    patient_id = request.form.get("patient_id", type=int)
    file = request.files.get("file")
    # ... logic
    return jsonify({...}), 201
```

#### Django:

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_http_methods(["POST"])
def create_sample(request):
    patient_id = request.POST.get("patient_id")
    file = request.FILES.get("file")
    # ... logic
    return JsonResponse({...}, status=201)
```

### 5. Service Layer Changes

#### Flask/SQLAlchemy:

```python
from ...extensions import db

class SampleService:
    @staticmethod
    def get_sample(sample_id: int) -> Optional[Sample]:
        return Sample.query.get(sample_id)

    @staticmethod
    def get_all_samples() -> list[Sample]:
        return Sample.query.all()

    @staticmethod
    def add_sample(patient_id: int, file_storage) -> Sample:
        sample = Sample(patient_id=patient_id, bam_url=object_uri)
        db.session.add(sample)
        db.session.commit()
        return sample
```

#### Django:

```python
from .models import Sample

class SampleService:
    @staticmethod
    def get_sample(sample_id: str) -> Optional[Sample]:
        try:
            return Sample.objects.get(id=sample_id)
        except Sample.DoesNotExist:
            return None

    @staticmethod
    def get_all_samples() -> list[Sample]:
        return list(Sample.objects.all())

    @staticmethod
    def add_sample(patient_id: int, file_storage) -> Sample:
        sample = Sample.objects.create(
            patient_id=patient_id,
            bam_url=object_uri
        )
        return sample
```

### 6. Configuration

#### Flask (app/config.py):

```python
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://..."
```

#### Django (backend/settings.py):

```python
import os

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DB', 'cnv_db'),
        'USER': os.getenv('MYSQL_USER', 'cnv_user'),
        # ...
    }
}
```

### 7. URL Routing

#### Flask:

```python
from flask import Blueprint
sample_bp = Blueprint("sample", __name__)

@sample_bp.post("/samples")
def create_sample():
    pass

# Register in app
app.register_blueprint(sample_bp, url_prefix="/api")
```

#### Django:

```python
# backend/features/sample/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('samples', views.create_sample, name='create_sample'),
]

# backend/urls.py
urlpatterns = [
    path('api/', include('backend.features.sample.urls')),
]
```

### 8. Migrations

#### Flask/Alembic:

```bash
flask --app app:create_app db init
flask --app app:create_app db migrate -m "description"
flask --app app:create_app db upgrade
```

#### Django:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 9. Running the Application

#### Flask:

```bash
flask run
# or
python run.py
```

#### Django:

```bash
python manage.py runserver
# or
python run.py
```

## Key Differences

1. **Database Access**: Django ORM vs SQLAlchemy
2. **Session Management**: Django auto-commits vs Flask manual commits
3. **File Handling**: `request.FILES` vs `request.files`
4. **JSON Responses**: `JsonResponse()` vs `jsonify()`
5. **Model Querying**: `Model.objects.get()` vs `Model.query.get()`
6. **CSRF Protection**: Requires `@csrf_exempt` for API views
7. **Configuration**: `settings.py` vs `Config` class
8. **URL Patterns**: `path()` vs decorators

## API Compatibility

All API endpoints remain the same:

- POST `/api/samples` - Create sample
- GET `/api/samples/` - List samples
- GET `/api/samples/<id>` - Get sample
- DELETE `/api/samples/<id>/delete` - Delete sample
- GET `/api/samples/<id>/file` - Download file

## Migration Steps for Existing Data

If you have existing data in MySQL:

1. Keep the old Flask code until migration is complete
2. The database schema should already be compatible
3. Run Django migrations: `python manage.py makemigrations`
4. Apply migrations: `python manage.py migrate`
5. Test all endpoints
6. Deploy Django version

## Testing

Test the migration:

```bash
# Start infrastructure
docker compose up -d

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Run server
python manage.py runserver

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/samples/
```
