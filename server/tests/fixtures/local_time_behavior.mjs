import { formatLocalTime } from "../../../web/assets/app.mjs";

const utcValue = "2023-11-14T22:13:20Z";
const output = formatLocalTime(utcValue);
const invalid = formatLocalTime("not-a-time");
if (!output || output === "Unknown reset time") throw new Error("valid local time");
if (invalid !== "Unknown reset time") throw new Error("invalid time fallback");
console.log(JSON.stringify({ output, invalid }));
