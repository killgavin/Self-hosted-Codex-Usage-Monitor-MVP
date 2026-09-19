const SAFE_STATES = new Set(["IDLE", "PENDING", "COMPLETED", "FAILED", "CANCELED"]);

function safeLabel(value, fallback) {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function safePercent(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? Math.max(0, Math.min(100, numeric)) : null;
}

function windowLabel(window, fallback) {
  if (window?.windowDurationMinutes === 300) return "5 Hours";
  if (window?.windowDurationMinutes === 10080) return "Weekly";
  return fallback;
}

/** Format canonical server UTC values in the browser's active locale/timezone. */
export function formatLocalTime(value) {
  if (typeof value !== "string" || !value) return "Unknown reset time";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown reset time";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function appendResetTime(document, section, value) {
  if (value === null || value === undefined) return;
  const row = document.createElement("p");
  row.className = "reset-time";
  const prefix = document.createElement("span");
  prefix.textContent = "Resets ";
  row.appendChild(prefix);
  const time = document.createElement("time");
  const formatted = formatLocalTime(value);
  time.textContent = formatted;
  if (formatted !== "Unknown reset time") time.setAttribute("datetime", value);
  row.appendChild(time);
  section.appendChild(row);
}

function appendWindow(document, card, window, fallbackLabel) {
  const section = document.createElement("section");
  section.className = "rate-limit-window";
  const heading = document.createElement("h4");
  heading.textContent = windowLabel(window, fallbackLabel);
  section.appendChild(heading);
  if (!window) {
    const unavailable = document.createElement("p");
    unavailable.textContent = "Not available";
    section.appendChild(unavailable);
    card.appendChild(section);
    return;
  }

  const used = safePercent(window.usedPercent);
  const remaining = safePercent(window.remainingPercent);
  const summary = document.createElement("p");
  summary.className = "rate-limit-summary";
  summary.textContent = used === null || remaining === null
    ? "Usage unavailable"
    : `${used}% used · ${remaining}% remaining`;
  section.appendChild(summary);

  const progress = document.createElement("progress");
  progress.max = 100;
  progress.value = remaining ?? 0;
  progress.setAttribute("aria-label", `${heading.textContent} remaining percentage`);
  section.appendChild(progress);
  appendResetTime(document, section, window.resetAt);
  card.appendChild(section);
}

/** Build one generic, text-only card from the stable REST rate-limit schema. */
export function createRateLimitCard(document, limit = {}) {
  const card = document.createElement("article");
  card.className = "rate-limit-card";
  const heading = document.createElement("h3");
  heading.textContent = safeLabel(limit.name, safeLabel(limit.id, "Unknown limit"));
  card.appendChild(heading);
  appendWindow(document, card, limit.primary, "Primary");
  appendWindow(document, card, limit.secondary, "Secondary");
  return card;
}

/** Replace a list with one card per limit, without interpreting unknown fields. */
export function renderRateLimitCards(document, container, limits) {
  container.replaceChildren();
  if (!Array.isArray(limits) || limits.length === 0) {
    const empty = document.createElement("p");
    empty.textContent = "No rate limits available.";
    container.appendChild(empty);
    return;
  }
  for (const limit of limits) container.appendChild(createRateLimitCard(document, limit));
}

function safeVerificationUrl(value) {
  // Only activate ordinary web links; never turn protocol-controlled schemes into hrefs.
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:" ? parsed.href : null;
  } catch {
    return null;
  }
}

/** Build the login view around injected DOM, network, and reload effects for safe testing. */
export function createLoginUI({ document, fetchImpl, reload, schedule = setTimeout }) {
  const elements = {
    state: document.getElementById("login-state"),
    error: document.getElementById("login-error"),
    device: document.getElementById("device-code"),
    link: document.getElementById("verification-link"),
    codeLabel: document.getElementById("user-code-label"),
    code: document.getElementById("user-code"),
    login: document.getElementById("login-button"),
    cancel: document.getElementById("cancel-button"),
    logout: document.getElementById("logout-button"),
  };
  let previousState = null;
  let reloadDone = false;
  let pollScheduled = false;

  function render(status) {
    // Render only the stable login fields; unknown protocol fields never enter the DOM.
    const state = SAFE_STATES.has(status?.state) ? status.state : "IDLE";
    elements.state.textContent = state;
    elements.error.hidden = true;
    const pending = state === "PENDING";
    const completed = state === "COMPLETED";
    elements.device.hidden = !pending;
    elements.login.hidden = pending || completed;
    elements.logout.hidden = !completed;
    elements.codeLabel.hidden = !pending || !status?.userCode;
    elements.code.textContent = pending ? (status.userCode || "") : "";
    const url = pending ? safeVerificationUrl(status.verificationUrl) : null;
    elements.link.hidden = !url;
    if (url) elements.link.href = url;
    else elements.link.removeAttribute("href");
    if (previousState === "PENDING" && state === "COMPLETED" && !reloadDone) {
      reloadDone = true;
      reload();
    }
    previousState = state;
    if (pending && !pollScheduled) {
      pollScheduled = true;
      schedule(() => { pollScheduled = false; refresh(); }, 500);
    }
  }

  function showError(message) {
    elements.error.textContent = typeof message === "string" && message ? message : "Request failed";
    elements.error.hidden = false;
  }

  async function request(path, method = "GET") {
    // Keep browser traffic on the server-owned login API and expose only its safe message.
    const response = await fetchImpl(path, { method });
    const body = await response.json();
    if (!response.ok) throw new Error(body?.error?.message || "Request failed");
    return body;
  }

  async function run(path, method) {
    elements.login.disabled = true;
    elements.cancel.disabled = true;
    elements.logout.disabled = true;
    try { render(await request(path, method)); }
    catch (error) { showError(error?.message); }
    finally {
      elements.login.disabled = false;
      elements.cancel.disabled = false;
      elements.logout.disabled = false;
    }
  }

  async function refresh() { await run("/api/v1/login/status"); }
  elements.login.addEventListener("click", () => run("/api/v1/login", "POST"));
  elements.cancel.addEventListener("click", () => run("/api/v1/login/cancel", "POST"));
  elements.logout.addEventListener("click", () => run("/api/v1/logout", "POST"));

  return { render, refresh, run };
}

if (typeof document !== "undefined") {
  createLoginUI({
    document,
    fetchImpl: (...args) => fetch(...args),
    reload: () => window.location.reload(),
  }).refresh();
}
