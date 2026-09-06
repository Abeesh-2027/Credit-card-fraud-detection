const form = document.getElementById("loginForm");
const nameInput = document.getElementById("name");
const passwordInput = document.getElementById("password");
const loginButton = document.getElementById("loginButton");
const loginButtonText = document.getElementById("loginButtonText");
const errorMessage = document.getElementById("errorMessage");

if (getToken()) {
  window.location.href = "dashboard.html";
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.classList.add("visible");
}

function clearError() {
  errorMessage.textContent = "";
  errorMessage.classList.remove("visible");
  nameInput.classList.remove("input-error");
  passwordInput.classList.remove("input-error");
}

function setLoading(isLoading) {
  loginButton.disabled = isLoading;
  loginButtonText.textContent = isLoading ? "Logging in…" : "Login";
}

form.addEventListener("submit", async function (event) {
  event.preventDefault();
  clearError();

  const name = nameInput.value.trim();
  const password = passwordInput.value.trim();

  if (name === "") {
    showError("Please enter your name.");
    nameInput.classList.add("input-error");
    nameInput.focus();
    return;
  }
  if (!/^\d{5}$/.test(password)) {
    showError("Please enter a five digit password.");
    passwordInput.classList.add("input-error");
    passwordInput.focus();
    return;
  }

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: name, password: password }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      showError(data.detail || "Login failed. Please check your name and password.");
      passwordInput.classList.add("input-error");
      setLoading(false);
      return;
    }

    const data = await response.json();
    setSession(data.access_token, data.username);
    window.location.href = "dashboard.html";
  } catch (err) {
    showError("Couldn't reach the server. Check your connection and try again.");
    setLoading(false);
  }
});
