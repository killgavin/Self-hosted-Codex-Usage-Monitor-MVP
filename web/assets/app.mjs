const SAFE_STATES = new Set(["IDLE", "PENDING", "COMPLETED", "FAILED", "CANCELED"]);

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
