# AbaNtu Job Centre Frontend

Mobile-first React/Vite marketplace timeline connected to the Django API.

## Start in PowerShell

```powershell
cd jobcentre-frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Keep Django running at `http://127.0.0.1:8000` and open the Vite URL, normally `http://localhost:5173`.

## Included

- Familiar marketplace timeline and responsive three-column desktop layout
- Mobile bottom navigation
- Public job search and browsing
- Job details with image, video and PDF rendering
- Employer/job-seeker registration and JWT login
- Employer dashboard and multi-file job posting
- Saved jobs and applications
- Automatic access-token refresh
- Profile editing and employer verification status
- Employer applicant review and status management
- Job reporting, pilot feedback and account deletion
- Privacy/Terms acceptance and password reset
- Private-pilot invitation code support
- Review-before-submit application form
- Atomic CV/application submission and duplicate-safe retry
- Permanent application references and confirmation
- Status timeline, withdrawal and CV replacement
- In-app notification centre and communication preferences
- Optional profile/organisation images with preview and initials fallback
- Empty, loading and error states

## Upload limits

- JPG, PNG and WebP: 8 MB each
- MP4 and WebM: 50 MB each
- Job PDFs and applicant PDFs: 10 MB each

Local files use Django media storage. Before public deployment, configure private cloud/object storage, signed document URLs, malware scanning and retention/deletion rules—especially for applicant documents.
