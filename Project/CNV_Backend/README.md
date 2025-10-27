## CNV Backend (Django)

Feature-driven Django backend using Django ORM, migrations, and MinIO for file storage.

### Quick Start

1. **Start infrastructure:**

   ```bash
   docker compose up -d
   ```

2. **Create virtual environment and install dependencies:**

   Windows:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

   Linux/Mac:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set environment variables (Optional):**

   Create a `.env` file in the project root or set these environment variables:

   ```env
   SECRET_KEY=your-secret-key-here
   MYSQL_HOST=localhost
   MYSQL_USER=cnv_user
   MYSQL_PASSWORD=cnv_pass
   MYSQL_DB=cnv_db
   MYSQL_PORT=3306
   MINIO_ENDPOINT=localhost:9000
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=minioadmin
   MINIO_BUCKET=cnv-bucket
   MINIO_USE_SSL=false
   ```

4. **Run database migrations:**

   First time setup (creates migration files):

   ```bash
   python manage.py makemigrations
   ```

   Apply migrations to database:

   ```bash
   python manage.py migrate
   ```

   For future model changes:

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser (optional, for Django admin):**

   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server:**

   ```bash
   python manage.py runserver
   # Or using the run.py file
   python run.py
   ```

   The server will be available at `http://localhost:8000`

### Project Structure

```
backend/                      # Django project root
├── settings.py              # Django settings
├── urls.py                  # Main URL configuration
├── wsgi.py                  # WSGI application
├── asgi.py                  # ASGI application
├── features/                # Feature modules
│   ├── sample/              # Sample management app
│   │   ├── models.py        # Django models
│   │   ├── views.py         # View functions
│   │   ├── urls.py         # URL routing
│   │   ├── service.py      # Business logic
│   │   ├── admin.py        # Admin interface
│   │   └── apps.py         # App configuration
│   └── algorithm/           # Algorithm app
│       ├── models.py
│       └── apps.py
└── utils/                   # Utility modules
    └── minio_utils.py       # MinIO file operations
```

### API Endpoints

All API endpoints are prefixed with `/api`

#### Sample Management

- **POST** `/api/samples` - Create a new sample
  - Form data: `patient_id` (int), `file` (BAM file)
- **GET** `/api/samples/` - List all samples
- **GET** `/api/samples/<sample_id>` - Get a specific sample
- **DELETE** `/api/samples/<sample_id>/delete` - Delete a sample
- **GET** `/api/samples/<sample_id>/file` - Download the BAM file for a sample

#### Health Check

- **GET** `/health` - Server health check endpoint

### Django ORM vs SQLAlchemy

This project has been migrated from Flask (SQLAlchemy) to Django:

| Flask/SQLAlchemy       | Django ORM                                          |
| ---------------------- | --------------------------------------------------- |
| `db.Model`             | `models.Model`                                      |
| `db.Column()`          | `models.CharField()`, `models.IntegerField()`, etc. |
| `Sample.query.get(id)` | `Sample.objects.get(id=id)`                         |
| `Sample.query.all()`   | `Sample.objects.all()`                              |
| `db.session.add()`     | `Model.objects.create()` or `model.save()`          |
| `db.session.commit()`  | Auto-committed in Django                            |
| `Alembic` migrations   | `python manage.py makemigrations` / `migrate`       |

### Database

- MySQL 8.0
- Configured via environment variables
- Managed through Django ORM and migrations

### File Storage

- MinIO for BAM file storage
- Files stored with URI format: `minio://bucket/path/to/file`
- Integrated with Django settings

### Development

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Run tests (when available)
python manage.py test

# Start development server
python manage.py runserver

# Start development server on custom port
python manage.py runserver 0.0.0.0:8000

# Access Django admin
# Navigate to http://localhost:8000/admin
```

### Docker Infrastructure

The project uses Docker Compose for infrastructure:

- **MySQL**: Database server on port 3306
- **MinIO**: Object storage server on port 9000 (API) and 9001 (Console)

Access MinIO console at `http://localhost:9001`

### Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/) (for building REST APIs)
- [MinIO Documentation](https://min.io/docs/)
