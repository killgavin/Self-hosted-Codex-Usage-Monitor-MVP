import { createRateLimitCard, renderRateLimitCards } from "../../../web/assets/app.mjs";

class Element {
  constructor(tagName) {
    this.tagName = tagName;
    this.children = [];
    this.textContent = "";
    this.className = "";
    this.attributes = {};
    this.max = null;
    this.value = null;
  }
  appendChild(child) { this.children.push(child); return child; }
  replaceChildren(...children) { this.children = children; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
}

const document = { createElement: (tagName) => new Element(tagName) };
const container = new Element("div");
const limits = [
  {
    id: "known-id",
    name: "Team limit",
    primary: { usedPercent: "25", remainingPercent: "75", windowDurationMinutes: 300 },
    secondary: { usedPercent: "50", remainingPercent: "50", windowDurationMinutes: 10080 },
  },
  {
    id: "future-limit",
    name: null,
    primary: { usedPercent: "12.5", remainingPercent: "87.5", windowDurationMinutes: 42 },
    secondary: null,
    futureProtocolField: "must-not-render",
  },
];

renderRateLimitCards(document, container, limits);
if (container.children.length !== 2) throw new Error("generic card count");
const known = container.children[0];
if (known.className !== "rate-limit-card" || known.children[0].textContent !== "Team limit") throw new Error("known card title");
if (known.children[1].children[0].textContent !== "5 Hours") throw new Error("five-hour label");
if (known.children[2].children[0].textContent !== "Weekly") throw new Error("weekly label");
if (known.children[1].children[2].value !== 75) throw new Error("remaining progress");

const future = container.children[1];
if (future.children[0].textContent !== "future-limit") throw new Error("unknown id fallback");
if (future.children[1].children[0].textContent !== "Primary") throw new Error("generic duration fallback");
if (future.children[2].children[1].textContent !== "Not available") throw new Error("nullable window");
if (JSON.stringify(future).includes("must-not-render")) throw new Error("unknown raw field rendered");

const unnamed = createRateLimitCard(document, { id: null, name: null });
if (unnamed.children[0].textContent !== "Unknown limit") throw new Error("unknown title fallback");

renderRateLimitCards(document, container, []);
if (container.children.length !== 1 || container.children[0].textContent !== "No rate limits available.") throw new Error("empty state");
console.log("rate-limit-card-behavior: PASS");
