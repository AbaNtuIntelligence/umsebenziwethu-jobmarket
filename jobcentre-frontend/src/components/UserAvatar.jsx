import { GoogleLogin } from "@react-oauth/google";
import { getMicrosoftIdToken } from "../services/socialAuth";

export default function SocialSignInButtons({
  onCredential,
  disabled = false,
  label = "Continue",
}) {
  const googleConfigured = Boolean(
    import.meta.env.VITE_GOOGLE_CLIENT_ID
  );

  const microsoftConfigured = Boolean(
    import.meta.env.VITE_MICROSOFT_CLIENT_ID
  );

  async function continueWithMicrosoft() {
    try {
      const token = await getMicrosoftIdToken();

      await onCredential(
        "microsoft",
        token
      );
    } catch (error) {
      await onCredential(
        null,
        null,
        error
      );
    }
  }

  const providersConfigured =
    googleConfigured ||
    microsoftConfigured;

  if (!providersConfigured) {
    return (
      <div className="social-auth-notice">
        <strong>Online account sign-in is coming shortly.</strong>

        <span>
          Existing pilot members can continue using email and password below.
        </span>
      </div>
    );
  }

  return (
    <div
      className="social-auth-buttons"
      aria-label="Account sign-in options"
    >
      {googleConfigured && (
        <GoogleLogin
          onSuccess={response =>
            onCredential(
              "google",
              response.credential
            )
          }
          onError={() =>
            onCredential(
              null,
              null,
              new Error(
                "Google sign-in was cancelled or could not be completed."
              )
            )
          }
          text={
            label === "Sign up"
              ? "signup_with"
              : "continue_with"
          }
          width="360"
        />
      )}

      {microsoftConfigured && (
        <button
          type="button"
          className="social-provider microsoft"
          onClick={continueWithMicrosoft}
          disabled={disabled}
        >
          <span
            className="microsoft-mark"
            aria-hidden="true"
          >
            <i />
            <i />
            <i />
            <i />
          </span>

          {label} with Microsoft
        </button>
      )}
    </div>
  );
}