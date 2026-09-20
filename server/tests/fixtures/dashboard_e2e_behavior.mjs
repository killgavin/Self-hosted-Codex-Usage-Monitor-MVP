import { createDashboardUI } from "../../../web/assets/app.mjs";

class Element {
  constructor(tagName) {
    this.tagName = tagName; this.children = []; this.textContent = "";
    this.value = ""; this.disabled = false; this.id = ""; this.attributes = {}; this.handlers = {};
  }
  appendChild(child) { this.children.push(child); return child; }
  replaceChildren(...children) { this.children = children; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  addEventListener(name, handler) { this.handlers[name] = handler; }
  async click() { await this.handlers.click?.(); }
}

const elements = new Map([
  ["server-token", new Element("input")], ["connect-button", new Element("button")],
  ["connection-status", new Element("p")], ["account-summary", new Element("section")],
  ["reset-credit-summary", new Element("section")], ["rate-limit-list", new Element("div")],
  ["last-updated", new Element("time")],
]);
const document = {
  getElementById: (id) => elements.get(id),
  createElement: (tagName) => new Element(tagName),
};
const token = "synthetic-server-token";
elements.get("server-token").value = token;
const calls = [];
let failing = false;
const responses = {
  "/api/v1/status": { status: "ok", privateField: "must-not-render" },
  "/api/v1/account": { authenticated: true, authMode: "stored", planType: "pro", privateField: "must-not-render" },
  "/api/v1/rate-limits": {
    limits: [{ id: "team", name: "Team limit", primary: { usedPercent: "20", remainingPercent: "80", windowDurationMinutes: 300, resetAt: "2023-11-14T22:13:20Z" }, secondary: null }],
    resetCredits: { availableCount: 2, credits: null },
    privateField: "must-not-render",
  },
};
const ui = createDashboardUI({
  document,
  now: () => new Date("2023-11-14T22:13:20Z"),
  fetchImpl: async (path, options) => {
    calls.push({ path, options });
    if (failing) return { ok: false, json: async () => ({ error: { message: "raw-private-error" } }) };
    return { ok: true, json: async () => responses[path] };
  },
});
await elements.get("connect-button").click();
if (elements.get("connection-status").textContent !== "Connected") throw new Error("connected state");
if (elements.get("server-token").value !== "") throw new Error("token retained");
if (elements.get("account-summary").children[0].id !== "account-title") throw new Error("account heading id");
if (elements.get("reset-credit-summary").children[0].id !== "reset-credit-title") throw new Error("reset heading id");
if (elements.get("account-summary").children[1].children[1].textContent !== "Yes") throw new Error("account rendering");
if (elements.get("reset-credit-summary").children[1].children[1].textContent !== "2") throw new Error("reset count");
if (elements.get("rate-limit-list").children.length !== 1) throw new Error("rate cards");
if (elements.get("last-updated").textContent === "Never") throw new Error("last updated");
if (calls.length !== 3 || calls.some(({ options }) => options.method !== "GET" || options.headers.Authorization !== `Bearer ${token}`)) throw new Error("authenticated calls");
const rendered = JSON.stringify([...elements.values()]);
if (["privateField", "must-not-render", "raw-private-error"].some((marker) => rendered.includes(marker))) throw new Error("raw field leak");
failing = true;
elements.get("server-token").value = token;
await elements.get("connect-button").click();
if (elements.get("connection-status").textContent !== "Connection failed") throw new Error("safe failure state");
if (elements.get("connect-button").disabled || elements.get("server-token").value !== "") throw new Error("failure cleanup");
const failedRendered = JSON.stringify([...elements.values()]);
if (failedRendered.includes("raw-private-error")) throw new Error("error leak");
const callsBeforeWhitespace = calls.length;
elements.get("server-token").value = "   ";
await elements.get("connect-button").click();
if (calls.length !== callsBeforeWhitespace || elements.get("server-token").value !== "") throw new Error("whitespace token");
console.log("dashboard-e2e-behavior: PASS");
