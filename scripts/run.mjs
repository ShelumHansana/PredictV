// One entry point for every npm script. It has no dependencies of its own, so
// `npm run dev` works on a fresh copy of the project without `npm install` first.
//
//   dev             set everything up if needed, then run the API and the React app together
//   build           build the React app into frontend/dist
//   start           build, then serve the API and the built app from one port (production style)
//   test            backend tests + frontend type check
//   train           retrain the exhaust-gas model
//   train-symptoms  train the learned symptom model from saved mechanic feedback

import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import http from "node:http";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const BACKEND = path.join(ROOT, "backend");
const FRONTEND = path.join(ROOT, "frontend");
const VENV = path.join(ROOT, ".venv");
const WIN = process.platform === "win32";
const VENV_PY = WIN ? path.join(VENV, "Scripts", "python.exe") : path.join(VENV, "bin", "python");
const VITE = path.join(FRONTEND, "node_modules", "vite", "bin", "vite.js");
const TSC = path.join(FRONTEND, "node_modules", "typescript", "bin", "tsc");

const say = msg => console.log(`\x1b[36m[predictv]\x1b[0m ${msg}`);
const fail = msg => { console.error(`\n\x1b[31m[predictv] ${msg}\x1b[0m\n`); process.exit(1); };

/** Run a command and wait for it. Stops the script if it fails. */
function run(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, { stdio: "inherit", ...opts });
  if (r.error) fail(`Could not run "${cmd}": ${r.error.message}`);
  if (r.status !== 0) fail(`"${cmd} ${args.join(" ")}" failed (exit code ${r.status}).`);
}
const quiet = (cmd, args, opts = {}) => spawnSync(cmd, args, { encoding: "utf8", ...opts });

// ── setup steps (each one is skipped when already done) ──────────────────────

function checkNode() {
  const major = Number(process.versions.node.split(".")[0]);
  if (major < 18) fail(`Node.js 18 or newer is needed (you have ${process.versions.node}). Get it from https://nodejs.org`);
}

function findPython() {
  const candidates = WIN ? [["python", []], ["py", ["-3"]]] : [["python3", []], ["python", []]];
  for (const [cmd, pre] of candidates) {
    const r = quiet(cmd, [...pre, "-c", "import sys; print(sys.version_info[0], sys.version_info[1])"]);
    if (r.status === 0) {
      const [major, minor] = r.stdout.trim().split(" ").map(Number);
      if (major === 3 && minor >= 10) return { cmd, pre, version: `${major}.${minor}` };
    }
  }
  fail("Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/ (on Windows tick \"Add python.exe to PATH\"), then run this again.");
}

function ensureVenv() {
  if (existsSync(VENV_PY)) return;
  const py = findPython();
  say(`Creating a Python ${py.version} environment in .venv (first run only)`);
  run(py.cmd, [...py.pre, "-m", "venv", VENV]);
}

function ensurePythonPackages() {
  const reqFile = path.join(BACKEND, "requirements.txt");
  const hash = createHash("sha1").update(readFileSync(reqFile)).digest("hex");
  const marker = path.join(VENV, ".requirements-installed");
  if (existsSync(marker) && readFileSync(marker, "utf8") === hash) return;
  say("Installing Python packages (first run only, takes a minute or two)");
  run(VENV_PY, ["-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", reqFile]);
  writeFileSync(marker, hash);
}

/** The saved models only load with the scikit-learn version they were trained with. */
function ensureModels() {
  const check = [
    "import json, pathlib, sys, sklearn",
    "d = pathlib.Path('models')",
    "ok = all((d / f).exists() for f in ('metrics.json', 'mixture_full.joblib', 'mixture_basic.joblib'))",
    "ok = ok and json.loads((d / 'metrics.json').read_text()).get('sklearn_version') == sklearn.__version__",
    "sys.exit(0 if ok else 3)",
  ].join("\n");
  if (quiet(VENV_PY, ["-c", check], { cwd: BACKEND }).status === 0) return;
  say("Training the model for your scikit-learn version (about a minute)");
  run(VENV_PY, [path.join("ml", "train.py")], { cwd: BACKEND });
}

function ensureNodePackages() {
  const lock = path.join(FRONTEND, "package-lock.json");
  const marker = path.join(FRONTEND, "node_modules", ".predictv-installed");
  const hash = createHash("sha1").update(readFileSync(lock)).digest("hex");
  if (existsSync(VITE) && existsSync(marker) && readFileSync(marker, "utf8") === hash) return;
  say("Installing frontend packages (first run only)");
  run("npm", ["install", "--no-audit", "--no-fund"], { cwd: FRONTEND, shell: true });
  writeFileSync(marker, hash);
}

function setup({ frontend = true } = {}) {
  checkNode();
  ensureVenv();
  ensurePythonPackages();
  ensureModels();
  if (frontend) ensureNodePackages();
}

// ── running servers ──────────────────────────────────────────────────────────

function freePort(start) {
  return new Promise(resolve => {
    const tryPort = port => {
      const server = net.createServer();
      server.once("error", () => tryPort(port + 1));
      server.once("listening", () => server.close(() => resolve(port)));
      server.listen(port, "127.0.0.1");
    };
    tryPort(start);
  });
}

function waitForApi(port, child) {
  return new Promise(resolve => {
    const started = Date.now();
    const attempt = () => {
      if (child.exitCode !== null) return resolve(false);
      const req = http.get({ host: "127.0.0.1", port, path: "/health", timeout: 1500 }, res => {
        res.resume();
        res.statusCode === 200 ? resolve(true) : retry();
      });
      req.on("error", retry);
      req.on("timeout", () => { req.destroy(); });
    };
    const retry = () => (Date.now() - started > 90_000 ? resolve(false) : setTimeout(attempt, 400));
    attempt();
  });
}

const children = [];
function start(name, color, cmd, args, opts) {
  const child = spawn(cmd, args, { stdio: ["ignore", "pipe", "pipe"], detached: !WIN, ...opts });
  const tag = `\x1b[${color}m[${name}]\x1b[0m `;
  const pipe = stream => {
    let rest = "";
    stream.on("data", chunk => {
      const lines = (rest + chunk).split(/\r?\n/);
      rest = lines.pop();
      for (const line of lines) if (line.trim()) console.log(tag + line);
    });
  };
  pipe(child.stdout);
  pipe(child.stderr);
  children.push(child);
  child.on("exit", code => { if (!stopping) { console.log(`${tag}stopped (exit code ${code})`); stopAll(code ?? 1); } });
  return child;
}

let stopping = false;
function stopAll(code = 0) {
  if (stopping) return;
  stopping = true;
  for (const child of children) {
    if (child.exitCode !== null || !child.pid) continue;
    try {
      if (WIN) spawnSync("taskkill", ["/pid", String(child.pid), "/T", "/F"], { stdio: "ignore" });
      else process.kill(-child.pid, "SIGTERM");
    } catch { /* already gone */ }
  }
  setTimeout(() => process.exit(code), 300);
}
process.on("SIGINT", () => stopAll(0));
process.on("SIGTERM", () => stopAll(0));

async function dev() {
  setup();
  const apiPort = await freePort(8000);
  say("Starting the API…");
  const apiProcess = start("api", 35, VENV_PY, ["-m", "uvicorn", "app.main:app", "--reload", "--reload-dir", "app", "--host", "127.0.0.1", "--port", String(apiPort)], { cwd: BACKEND });
  if (!(await waitForApi(apiPort, apiProcess))) { stopAll(1); fail("The API did not start. See the [api] lines above."); }
  const webPort = await freePort(5173);
  start("web", 32, process.execPath, [VITE, "--port", String(webPort), "--strictPort", "--host", "127.0.0.1"], { cwd: FRONTEND, env: { ...process.env, PREDICTV_API_PORT: String(apiPort) } });
  say(`Ready. Open  http://localhost:${webPort}   (API docs: http://localhost:${apiPort}/docs)   Press Ctrl+C to stop.`);
}

function build() {
  checkNode();
  ensureNodePackages();
  run(process.execPath, [TSC, "--noEmit"], { cwd: FRONTEND });
  run(process.execPath, [VITE, "build"], { cwd: FRONTEND });
}

async function serve() {
  setup();
  build();
  const port = Number(process.env.PORT) || (await freePort(8000));
  const host = process.env.HOST || "127.0.0.1";
  const apiProcess = start("app", 35, VENV_PY, ["-m", "uvicorn", "app.main:app", "--host", host, "--port", String(port)], { cwd: BACKEND });
  if (!(await waitForApi(port, apiProcess))) { stopAll(1); fail("The app did not start. See the [app] lines above."); }
  say(`Ready. Open  http://localhost:${port}   Press Ctrl+C to stop.`);
}

function test() {
  setup();
  say("Backend tests");
  run(VENV_PY, ["-m", "pytest", "-q", "tests"], { cwd: BACKEND });
  say("Frontend type check");
  run(process.execPath, [TSC, "--noEmit"], { cwd: FRONTEND });
  say("All checks passed.");
}

const command = process.argv[2] ?? "dev";
switch (command) {
  case "dev": await dev(); break;
  case "build": build(); break;
  case "start": await serve(); break;
  case "test": test(); break;
  case "train": setup({ frontend: false }); run(VENV_PY, [path.join("ml", "train.py")], { cwd: BACKEND }); break;
  case "train-symptoms": setup({ frontend: false }); run(VENV_PY, [path.join("ml", "train_symptoms.py")], { cwd: BACKEND }); break;
  default: fail(`Unknown command "${command}".`);
}
