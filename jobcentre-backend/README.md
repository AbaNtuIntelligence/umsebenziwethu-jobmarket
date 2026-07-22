# AbaNtu Job Centre Backend

A privacy-conscious Django REST API for a South African jobs marketplace. Employers register and submit vacancies; job seekers browse, save and apply. New vacancies enter moderation as `pending` before an administrator publishes them.

## Included

- Employer and job-seeker roles
- JWT login and refresh tokens
- Employer and job-seeker profiles
- Public job browsing, search, filters and pagination
- Employer-owned job creation, editing and closing
- Admin verification and vacancy moderation
- Applications with employer-controlled statuses
- Saved jobs
- Employer job media: JPG, PNG, WebP, MP4, WebM and PDF
- Private PDF application documents
- Swagger API documentation
- SQLite locally and PostgreSQL in production
- CORS, secure production cookies and environment-based secrets
- Automated API tests
- Recorded Terms/Privacy consent
- Configurable private-pilot invitation code
- Employer applicant review and status updates
- Job reporting, user feedback and account deletion
- Password reset workflow
- Single-request, duplicate-safe application submission
- Application references, consent records and status history
- In-app notifications and transactional email hooks
- Protected CV downloads, CV replacement and withdrawal
- Optional validated user avatars with automatic file cleanup
- Provider-independent mobile OTP verification with hashed, expiring, single-use codes

## Start on Windows (Git Bash)

```bash
cd jobcentre-backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations accounts jobs
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

PowerShell activation: `.venv\\Scripts\\Activate.ps1`

Open:

- Health: http://127.0.0.1:8000/api/health/
- API docs: http://127.0.0.1:8000/api/docs/
- Admin: http://127.0.0.1:8000/admin/

## Main endpoints

| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/auth/register/` | Public |
| POST | `/api/auth/login/` | Public |
| POST | `/api/auth/token/refresh/` | Public |
| GET/PATCH | `/api/auth/me/` | Signed in |
| POST | `/api/auth/phone-otp/send/` | Signed in |
| POST | `/api/auth/phone-otp/verify/` | Signed in |
| GET/PATCH | `/api/auth/profile/` | Signed in |
| GET | `/api/jobs/` | Public |
| GET | `/api/jobs/{id}/` | Public |
| POST | `/api/jobs/` | Employer |
| GET | `/api/jobs/mine/` | Employer |
| POST | `/api/jobs/{id}/close/` | Job owner |
| GET/POST | `/api/applications/` | Signed in / job seeker |
| POST | `/api/applications/submit/` | Job seeker |
| GET | `/api/applications/{id}/` | Applicant or job owner |
| PATCH | `/api/applications/{id}/status/` | Job owner |
| POST | `/api/applications/{id}/withdraw/` | Applicant |
| PUT | `/api/applications/{id}/cv/` | Applicant |
| GET | `/api/application-documents/{id}/download/` | Applicant, job owner or admin |
| GET | `/api/notifications/` | Signed in |
| POST | `/api/notifications/{id}/read/` | Notification owner |
| POST | `/api/notifications/read-all/` | Signed in |
| GET/POST | `/api/saved-jobs/` | Job seeker |
| DELETE | `/api/saved-jobs/{job_id}/` | Job seeker |
| POST | `/api/jobs/{job_id}/media/` | Job owner |
| DELETE | `/api/job-media/{id}/` | Job owner |
| POST | `/api/applications/{id}/documents/` | Applicant |
| POST | `/api/job-reports/` | Public |
| POST | `/api/feedback/` | Public |
| POST | `/api/auth/password-reset/` | Public |
| POST | `/api/auth/password-reset-confirm/` | Public |
| POST | `/api/auth/delete-account/` | Signed in |

Search example: `/api/jobs/?search=driver&province=Gauteng&urgent=true&ordering=closing_date`

## Registration examples

Job seeker:

```json
{"email":"seeker@example.com","username":"seeker","phone":"0821234567","role":"job_seeker","password":"StrongPass778!","accept_terms":true}
```

Employer:

```json
{"email":"hr@example.com","username":"companyhr","phone":"0821234567","role":"employer","organisation_name":"Example Logistics","password":"StrongPass778!","accept_terms":true}
```

Login uses `email` and `password`. Send the returned access token as `Authorization: Bearer YOUR_TOKEN`.

## Reliable application submission

Send `multipart/form-data` to `/api/applications/submit/` with `job`, optional `cover_note`, optional PDF `cv`, and `consent_to_share=true`. The endpoint creates the application, document, consent timestamp, first history event and notifications in one transaction. A safe retry returns the existing application with `already_submitted=true` rather than creating a duplicate.

Every application receives a reference such as `APP-2026-A1B2C3D4`. CV download URLs require JWT authentication and verify that the requester is the applicant, job owner or an administrator.

## Profile images

Authenticated users can send a multipart `PATCH` to `/api/auth/me/` with an optional `avatar`. JPG, PNG and WebP are accepted up to 3 MB. Employer images appear on public job cards; job-seeker images are exposed only through applications submitted to the responsible employer. Images are optional and initials remain the fallback.

## Production

Set `DEBUG=False`, a long random `SECRET_KEY`, the public domain in `ALLOWED_HOSTS`, the frontend URL in `CORS_ALLOWED_ORIGINS`, and a PostgreSQL `DATABASE_URL`. Build command: `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`. Start command: `gunicorn config.wsgi:application`.

For a private pilot, also set `PILOT_INVITE_CODE` to a strong code shared only with invited participants and set `FRONTEND_URL` to the deployed frontend origin. Configure a real SMTP email backend before testing password reset outside localhost.

`render.yaml` is included as a deployment starting point. Do not deploy applicant documents to ephemeral local storage. Configure private persistent/object storage, signed access, malware scanning and retention rules first.

## Mobile OTP provider

OTP security and delivery are separated. Django creates a six-digit code, stores only its password hash, limits attempts and resends, expires it, and marks it single-use. The configured provider receives `phone`, `code` and `expires_minutes`, sends the SMS, and returns an optional `{"reference": "provider-message-id"}`.

Local development uses `accounts.phone_otp.ConsoleOTPProvider`, which writes the code to the backend console. It refuses to send when `DEBUG=False`. Before enabling verification on Render, set `PHONE_OTP_PROVIDER` to the dotted class path of an SMS adapter that follows this contract. Never expose the OTP in an API response or provider logs.

## Privacy baseline

This first version intentionally does not collect ID copies, banking details, special personal information or CV files. Add private CV storage only after access logging, retention/deletion rules, privacy notices and a security-incident process are in place.
