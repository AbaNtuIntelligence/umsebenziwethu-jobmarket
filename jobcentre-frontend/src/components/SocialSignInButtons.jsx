import { GoogleLogin } from "@react-oauth/google";

export default function SocialSignInButtons({
  onCredential,
  label = "Continue",
}) {
  const googleClientId =
    import.meta.env.VITE_GOOGLE_CLIENT_ID?.trim();

  if (!googleClientId) {
    return (
      <div className="social-auth-notice">
        <strong>Google sign-in is being configured.</strong>

        <span>
          Existing pilot members can temporarily use email and password below.
        </span>
      </div>
    );
  }

  return (
    <div
      className="social-auth-buttons"
      aria-label="Google account sign-in"
    >
      <GoogleLogin
        onSuccess={(response) =>
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
    </div>
  );
}