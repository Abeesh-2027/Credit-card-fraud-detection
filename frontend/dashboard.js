requireLoginOrRedirect();

const username = sessionStorage.getItem(AUTH_USER_KEY) || "analyst";
document.getElementById("userChip").textContent = username;

document.getElementById("logoutBtn").addEventListener("click", () => {
  clearSession();
  window.location.href = "index.html";
});

const form = document.getElementById("txnForm");
const analyzeBtn = document.getElementById("analyzeBtn");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");

const gauge = document.getElementById("gauge");
const gaugeValue = document.getElementById("gaugeValue");
const verdictBadge = document.getElementById("verdictBadge");
const signalsList = document.getElementById("signalsList");

const metricAuc = document.getElementById("metricAuc");
const metricPrecision = document.getElementById("metricPrecision");
const metricRecall = document.getElementById("metricRecall");

const TIER_COLORS = {
  low: "var(--safe)",
  elevated: "var(--elevated)",
  high: "var(--high)",
  critical: "var(--critical)",
};


async function apiFetch(path, options = {}) {
  const token = getToken();
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  if (response.status === 401) {
    clearSession();
    window.location.href = "index.html";
    throw new Error("Session expired");
  }
  return response;
}

// --- Model status + metrics on load ---
async function loadModelInfo() {
  try {
    const res = await apiFetch("/api/model-info");
    if (!res.ok) throw new Error("model-info failed");
    const data = await res.json();

    statusDot.classList.add("ready");
    statusText.textContent = `model ready • AUC ${data.auc}`;

    metricAuc.textContent = data.auc.toFixed(3);
    metricPrecision.textContent = data.precision_fraud.toFixed(3);
    metricRecall.textContent = data.recall_fraud.toFixed(3);
  } catch (err) {
    statusDot.classList.add("error");
    statusText.textContent = "backend unreachable";
  }
}
loadModelInfo();

// --- Form -> API payload ---
function readForm() {
  return {
    amount: parseFloat(document.getElementById("amount").value),
    hour: parseFloat(document.getElementById("hour").value),
    distance_from_home_km: parseFloat(document.getElementById("distance_from_home_km").value),
    distance_from_last_txn_km: parseFloat(document.getElementById("distance_from_last_txn_km").value),
    ratio_to_median_spend: parseFloat(document.getElementById("ratio_to_median_spend").value),
    txns_last_24h: parseInt(document.getElementById("txns_last_24h").value, 10),
    is_foreign: document.getElementById("is_foreign").checked,
    is_online: document.getElementById("is_online").checked,
    is_new_merchant: document.getElementById("is_new_merchant").checked,
    card_present: document.getElementById("card_present").checked,
  };
}

function renderResult(result) {
  const pct = Math.round(result.fraud_probability * 100);
  gauge.style.setProperty("--pct", pct);
  gauge.style.setProperty("--tier-color", TIER_COLORS[result.risk_level] || "var(--text-faint)");
  gaugeValue.textContent = `${pct}%`;

  verdictBadge.textContent = result.is_fraud
    ? `FLAGGED — ${result.risk_level.toUpperCase()} RISK`
    : `CLEARED — ${result.risk_level.toUpperCase()} RISK`;
  verdictBadge.className = `verdict-badge ${result.risk_level}`;

  signalsList.innerHTML = "";
  if (!result.top_signals || result.top_signals.length === 0) {
    signalsList.innerHTML = '<li class="signal-placeholder">No strong signals detected.</li>';
    return;
  }

  const maxInfluence = Math.max(...result.top_signals.map((s) => s.influence), 0.0001);
  result.top_signals.forEach((signal) => {
    const li = document.createElement("li");
    li.className = "signal-row";

    const name = document.createElement("span");
    name.className = "signal-name";
    name.textContent = signal.feature.replace(/_/g, " ");

    const track = document.createElement("span");
    track.className = "signal-bar-track";
    const fill = document.createElement("span");
    fill.className = "signal-bar-fill";
    fill.style.width = `${(signal.influence / maxInfluence) * 100}%`;
    track.appendChild(fill);

    li.appendChild(name);
    li.appendChild(track);
    signalsList.appendChild(li);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  analyzeBtn.classList.add("loading");
  analyzeBtn.disabled = true;

  try {
    const payload = readForm();
    const res = await apiFetch("/api/predict", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert(err.detail || "Couldn't score this transaction. Please try again.");
      return;
    }

    const result = await res.json();
    renderResult(result);
  } catch (err) {
    if (err.message !== "Session expired") {
      alert("Couldn't reach the backend. Check your connection and try again.");
    }
  } finally {
    analyzeBtn.classList.remove("loading");
    analyzeBtn.disabled = false;
  }
});

// --- Presets ---
const PRESETS = {
  typical: {
    amount: 48.2, hour: 13, distance_from_home_km: 4, distance_from_last_txn_km: 2,
    ratio_to_median_spend: 0.9, txns_last_24h: 1,
    is_foreign: false, is_online: false, is_new_merchant: false, card_present: true,
  },
  suspicious: {
    amount: 1240, hour: 2, distance_from_home_km: 890, distance_from_last_txn_km: 760,
    ratio_to_median_spend: 9.4, txns_last_24h: 8,
    is_foreign: true, is_online: true, is_new_merchant: true, card_present: false,
  },
};

document.querySelectorAll(".preset-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const preset = PRESETS[btn.dataset.preset];
    if (!preset) return;
    Object.entries(preset).forEach(([key, value]) => {
      const el = document.getElementById(key);
      if (!el) return;
      if (el.type === "checkbox") el.checked = value;
      else el.value = value;
    });
  });
});
