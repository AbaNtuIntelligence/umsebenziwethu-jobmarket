import { PublicClientApplication } from "@azure/msal-browser";

const microsoftClientId = import.meta.env.VITE_MICROSOFT_CLIENT_ID;
const microsoftTenant = import.meta.env.VITE_MICROSOFT_TENANT || "common";
let microsoftApp;

function getMicrosoftApp() {
  if (!microsoftClientId) throw new Error("Microsoft sign-in has not been configured yet.");
  if (!microsoftApp) {
    microsoftApp = new PublicClientApplication({
      auth: {
        clientId: microsoftClientId,
        authority: `https://login.microsoftonline.com/${microsoftTenant}`,
        redirectUri: window.location.origin,
      },
      cache: { cacheLocation: "sessionStorage" },
    });
  }
  return microsoftApp;
}

export async function getMicrosoftIdToken() {
  const app = getMicrosoftApp();
  await app.initialize();
  const result = await app.loginPopup({
    scopes: ["openid", "profile", "email"],
    prompt: "select_account",
  });
  if (!result.idToken) throw new Error("Microsoft did not return an identity token.");
  return result.idToken;
}
