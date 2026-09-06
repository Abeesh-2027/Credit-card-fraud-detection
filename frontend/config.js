const PRODUCTION_API_BASE = "https://YOUR-BACKEND-NAME.onrender.com";

const API_BASE = (() => {
  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1") {
    return "http://127.0.0.1:8000";
  }
  return PRODUCTION_API_BASE;
})();

const AUTH_TOKEN_KEY = "fraudwatch_token";
const AUTH_USER_KEY = "fraudwatch_user";

function getToken() {
  return sessionStorage.getItem(AUTH_TOKEN_KEY);
}

function setSession(token, username) {
  sessionStorage.setItem(AUTH_TOKEN_KEY, token);
  sessionStorage.setItem(AUTH_USER_KEY, username);
}

function clearSession() {
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
  sessionStorage.removeItem(AUTH_USER_KEY);
}

function requireLoginOrRedirect() {
  if (!getToken()) {
    window.location.href = "index.html";
  }
}
