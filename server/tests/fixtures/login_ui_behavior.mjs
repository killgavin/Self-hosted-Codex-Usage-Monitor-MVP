import { createLoginUI } from "../../../web/assets/app.mjs";

class Element {
  constructor() { this.hidden = false; this.disabled = false; this.textContent = ""; this.href = ""; this.handlers = {}; }
  addEventListener(name, handler) { this.handlers[name] = handler; }
  async click() { if (this.handlers.click) await this.handlers.click(); }
  removeAttribute(name) { if (name === "href") this.href = ""; }
}

const elements = new Map([
  ["login-state", new Element()], ["login-error", new Element()], ["device-code", new Element()],
  ["verification-link", new Element()], ["user-code-label", new Element()], ["user-code", new Element()],
  ["login-button", new Element()], ["cancel-button", new Element()], ["logout-button", new Element()],
]);
const document = { getElementById: (id) => elements.get(id) };
let reloads = 0;
const calls = [];
const responses = [
  { state: "PENDING", verificationUrl: "https://safe.invalid", userCode: "login-code", loginId: "raw-id", future: "raw-extra" },
  { state: "CANCELED", loginId: "raw-id" },
  { state: "PENDING", verificationUrl: "https://safe.invalid", userCode: "login-code" },
  { state: "IDLE" },
  { state: "PENDING", verificationUrl: "https://safe.invalid", userCode: "login-code" },
];
const ui = createLoginUI({
  document,
  fetchImpl: async (path, options) => {
    calls.push([path, options.method]);
    return { ok: true, json: async () => responses.shift() };
  },
  reload: () => { reloads += 1; },
  schedule: () => 0,
});
const get = (id) => elements.get(id);

await get("login-button").click();
await get("cancel-button").click();
await get("login-button").click();
await get("logout-button").click();
await ui.refresh();
const expectedCalls = [
  ["/api/v1/login", "POST"], ["/api/v1/login/cancel", "POST"],
  ["/api/v1/login", "POST"], ["/api/v1/logout", "POST"],
  ["/api/v1/login/status", "GET"],
];
if (JSON.stringify(calls) !== JSON.stringify(expectedCalls)) throw new Error("REST calls");

ui.render({ state: "IDLE", verificationUrl: "https://safe.invalid", userCode: "old" });
if (get("login-button").hidden !== false || get("device-code").hidden !== true || get("user-code").textContent !== "") throw new Error("idle rendering");
ui.render({ state: "PENDING", verificationUrl: "https://safe.invalid/path", userCode: "safe-code", loginId: "raw-id", raw: "raw-extra" });
if (get("login-button").hidden !== true || get("device-code").hidden !== false || get("user-code").textContent !== "safe-code" || get("verification-link").href !== "https://safe.invalid/path") throw new Error("pending display");
if ([get("login-state"), get("user-code"), get("verification-link")].some((element) => JSON.stringify(element).includes("raw-id") || JSON.stringify(element).includes("raw-extra"))) throw new Error("raw field leak");
ui.render({ state: "PENDING", verificationUrl: "javascript:alert(1)", userCode: "safe-code" });
if (get("verification-link").hidden !== true || get("verification-link").href !== "") throw new Error("pending safety");
ui.render({ state: "FAILED", verificationUrl: "https://old.invalid", userCode: "old-code" });
if (get("device-code").hidden !== true || get("user-code").textContent !== "" || get("verification-link").href !== "") throw new Error("failed clearing");
ui.render({ state: "PENDING", verificationUrl: "https://safe.invalid/path", userCode: "code" });
ui.render({ state: "COMPLETED" });
ui.render({ state: "COMPLETED" });
if (reloads !== 1 || get("logout-button").hidden !== false || get("device-code").hidden !== true) throw new Error("completion transition");
console.log("login-ui-behavior: PASS");
