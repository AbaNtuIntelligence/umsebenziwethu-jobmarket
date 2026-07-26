# UmsebenziWethu Google and Microsoft sign-in

OTP has been removed. New accounts use Google or Microsoft OpenID Connect. Existing email/password accounts remain available during migration and can link a provider after confirming the current password once.

## 1. Google Cloud

1. Open Google Cloud Console and select or create the UmsebenziWethu project.
2. Configure the OAuth consent screen with the application name, support email, homepage, Privacy Notice and Terms links.
3. Create an OAuth 2.0 Client ID of type **Web application**.
4. Add these Authorized JavaScript origins:
   - `http://localhost:5173`
   - The deployed frontend origin, for example `https://umsebenziwethu.co.za`
5. Copy the Client ID. No Google client secret is needed by this implementation.

## 2. Microsoft Entra

1. Open Microsoft Entra admin centre → App registrations → New registration.
2. Select the supported account type that allows organisational directories and personal Microsoft accounts.
3. Under Authentication, add a **Single-page application** platform.
4. Add redirect URIs:
   - `http://localhost:5173`
   - The deployed frontend origin
5. Copy the Application (client) ID. No Microsoft client secret belongs in the frontend.

## 3. Local environment

Backend `jobcentre-backend/.env`:

```env
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
MICROSOFT_OAUTH_CLIENT_ID=your-microsoft-application-id
MICROSOFT_OAUTH_TENANT=common
```

Frontend `jobcentre-frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000/api
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_MICROSOFT_CLIENT_ID=your-microsoft-application-id
VITE_MICROSOFT_TENANT=common
```

The frontend and backend client IDs must match for each provider.

## 4. Apply the change

```powershell
cd jobcentre-backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py test accounts jobs
```

In a second terminal:

```powershell
cd jobcentre-frontend
npm install
npm run build
npm run dev
```

## 5. Render

Set the three backend variables on the API service and the three `VITE_` variables on the static frontend service. Vite variables are compiled at build time, so trigger a new frontend deployment after changing them.

Run the migration before serving the new backend release. Migration `accounts.0009_social_authentication` deletes OTP challenges and the old phone-verification field, then creates provider identities and authentication-event records.

## 6. Acceptance checks

- New job seeker can sign up with Google.
- New employer must provide an organisation name.
- New account must accept the Terms and Privacy Notice.
- New Microsoft account can sign up and log back in.
- Existing password account receives the safe linking prompt.
- Wrong linking password is rejected and recorded.
- Correct linking password attaches the provider and signs the user in.
- A social-only user can delete their account by typing `DELETE`.
- Employers remain unverified until the separate employer-review process is completed.
