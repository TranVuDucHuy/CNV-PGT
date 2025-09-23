## CNV Backend (Flask)

Feature-driven Flask app using SQLAlchemy, Alembic, and MinIO.

### Quick start

1. Start infra:
   - `docker compose up -d`
2. Create virtual env and install deps:
   - `python -m venv .venv && .venv\Scripts\activate` (Windows)
   - `pip install -r requirements.txt`
3. Set env (example):
   - `set FLASK_APP=app:create_app`
   - `set MYSQL_HOST=localhost`
   - `set MYSQL_USER=cnv_user`
   - `set MYSQL_PASSWORD=cnv_pass`
   - `set MYSQL_DB=cnv_db`
   - `set MINIO_ENDPOINT=localhost:9000`
   - `set MINIO_ACCESS_KEY=minioadmin`
   - `set MINIO_SECRET_KEY=minioadmin`
   - `set MINIO_BUCKET=cnv-bucket`
4. Initialize DB:

   - `flask --app app:create_app db init` (first time only if migrations/ absent)
   - `flask --app app:create_app db migrate -m "init"`
   - `flask --app app:create_app db upgrade`

5. Run app:
   - `flask run`

### API

- POST `/api/samples` form-data: `patient_id`, `file` (BAM)
- GET `/api/samples/<id>`
- DELETE `/api/samples/<id>`
