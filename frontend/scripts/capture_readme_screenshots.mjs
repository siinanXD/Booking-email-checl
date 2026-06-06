/**
 * Captures README UI screenshots (Playwright).
 * Usage (from frontend/): npm run screenshots:readme
 */
import { chromium } from "playwright";
import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, "..", "..");
const OUT_DIR = path.join(ROOT, "docs", "images", "screenshots");

const PRODUCTION_URL = "https://booking-email-checl-production.up.railway.app";

let BASE_URL = process.env.BASE_URL ?? "http://localhost:5173";
let API_URL = process.env.API_URL ?? BASE_URL;
let ADMIN_EMAIL = process.env.ADMIN_EMAIL;
let ADMIN_PASSWORD = process.env.ADMIN_PASSWORD;

function applyProductionDefaults() {
  if (!process.argv.includes("--production")) return;
  BASE_URL = process.env.BASE_URL ?? PRODUCTION_URL;
  API_URL = process.env.API_URL ?? BASE_URL;
}

function applyDemoDefaults() {
  const demoMode =
    process.env.SCREENSHOT_DEMO === "1" || process.argv.includes("--demo");
  if (!demoMode) return;
  BASE_URL = process.env.BASE_URL ?? "http://127.0.0.1:5098";
  API_URL = process.env.API_URL ?? BASE_URL;
  ADMIN_EMAIL = ADMIN_EMAIL ?? "admin@test.local";
  ADMIN_PASSWORD = ADMIN_PASSWORD ?? "test-password";
  process.env.TENANT_EMAIL = process.env.TENANT_EMAIL ?? "owner-mail@test.local";
  process.env.TENANT_PASSWORD = process.env.TENANT_PASSWORD ?? "secure-pass";
  process.env.SKIP_TENANT_SETUP = "1";
}

async function loadDotEnv() {
  const envPath = path.join(ROOT, ".env");
  const raw = await readFile(envPath, "utf8").catch(() => "");
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq < 0) continue;
    const key = trimmed.slice(0, eq).trim();
    let value = trimmed.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (key === "ADMIN_EMAIL" && !ADMIN_EMAIL) ADMIN_EMAIL = value;
    if (key === "ADMIN_PASSWORD" && !ADMIN_PASSWORD) ADMIN_PASSWORD = value;
    if (key === "URL" && !process.env.BASE_URL && !process.argv.includes("--production")) {
      BASE_URL = value;
      API_URL = value;
    }
    if (key === "TENANT_EMAIL" && !process.env.TENANT_EMAIL) {
      process.env.TENANT_EMAIL = value;
    }
    if (key === "TENANT_PASSWORD" && !process.env.TENANT_PASSWORD) {
      process.env.TENANT_PASSWORD = value;
    }
  }
}

const VIEWPORT = { width: 1440, height: 900 };

async function waitForApp(page) {
  await page.waitForLoadState("networkidle", { timeout: 30_000 }).catch(() => {});
  await page.waitForTimeout(800);
}

async function shot(page, name) {
  const file = path.join(OUT_DIR, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log(`saved ${file}`);
}

async function captureRoute(page, route, name, { selectFirst = false } = {}) {
  await page.goto(`${BASE_URL}${route}`, { waitUntil: "domcontentloaded" });
  await waitForApp(page);
  if (selectFirst === "review") {
    const reviewItem = page.locator("ul button").first();
    if (await reviewItem.count()) {
      await reviewItem.click();
      await waitForApp(page);
    }
  } else if (selectFirst === "table") {
    const row = page.locator("tbody tr").first();
    if (await row.count()) {
      await row.click();
      await waitForApp(page);
    }
  }
  await shot(page, name);
}

async function login(page, email, password) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded" });
  await waitForApp(page);
  await page.locator("#login-email").fill(email);
  await page.locator("#login-password").fill(password);
  await page.getByRole("button", { name: /anmelden/i }).click();
  await page.waitForURL((url) => !url.pathname.includes("/login"), { timeout: 20_000 });
  await waitForApp(page);
}

function requireAdminCreds() {
  if (!ADMIN_EMAIL || !ADMIN_PASSWORD) {
    throw new Error("ADMIN_EMAIL and ADMIN_PASSWORD must be set in the environment.");
  }
}

async function registerTenant() {
  requireAdminCreds();
  const loginRes = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: ADMIN_EMAIL, password: ADMIN_PASSWORD }),
  });
  if (!loginRes.ok) throw new Error(`Admin login failed: ${loginRes.status}`);
  const { access_token: token } = await loginRes.json();
  const headers = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  const email = `readme-tenant-${Date.now()}@example.com`;
  const password = "ReadmeTenant123!";
  const reg = await fetch(`${API_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      password_confirm: password,
      first_name: "Demo",
      last_name: "Mandant",
      phone: "+491701234567",
      account_type: "business",
      company_name: "Demo Hotel GmbH",
    }),
  });
  if (!reg.ok) {
    const errBody = await reg.text();
    throw new Error(`Register failed: ${reg.status} ${errBody}`);
  }

  const pending = await fetch(`${API_URL}/api/admin/accounts?status=pending`, { headers });
  const items = (await pending.json()).items ?? [];
  const tenant = items.find((i) => i.contact_email === email);
  if (!tenant) throw new Error("Pending tenant not found");

  const approve = await fetch(`${API_URL}/api/admin/accounts/${tenant.id}/approve`, {
    method: "POST",
    headers,
  });
  if (!approve.ok) throw new Error(`Approve failed: ${approve.status}`);

  await completeMailOnboarding(email, password);
  return { email, password };
}

async function completeMailOnboarding(email, password) {
  const loginRes = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!loginRes.ok) throw new Error(`Tenant login failed: ${loginRes.status}`);
  const { access_token: token } = await loginRes.json();
  const put = await fetch(`${API_URL}/api/mail/connection`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ onboarding_completed: true }),
  });
  if (!put.ok) throw new Error(`Onboarding skip failed: ${put.status}`);
}

async function captureTenantViews(page) {
  const tenantEmail = process.env.TENANT_EMAIL;
  const tenantPassword = process.env.TENANT_PASSWORD;
  let creds;
  if (tenantEmail && tenantPassword) {
    creds = { email: tenantEmail, password: tenantPassword };
  } else if (process.env.SKIP_TENANT_SETUP !== "1") {
    creds = await registerTenant();
  } else {
    console.log("Skipping tenant screenshots (SKIP_TENANT_SETUP=1, no TENANT_EMAIL).");
    return;
  }

  await login(page, creds.email, creds.password);
  await shot(page, "dashboard");

  await captureRoute(page, "/review", "review-queue", { selectFirst: "review" });
  await captureRoute(page, "/bookings", "bookings", { selectFirst: "table" });
  await captureRoute(page, "/settings", "settings");
}

async function main() {
  applyProductionDefaults();
  applyDemoDefaults();
  await loadDotEnv();
  API_URL = process.env.API_URL ?? BASE_URL;
  console.log(`Capturing screenshots from ${BASE_URL}`);
  await mkdir(OUT_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();

  try {
    await page.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded" });
    await waitForApp(page);
    await shot(page, "login");

    await page.goto(`${BASE_URL}/register`, { waitUntil: "domcontentloaded" });
    await waitForApp(page);
    await shot(page, "register");

    await captureTenantViews(page);

    if (process.env.SKIP_ADMIN_SCREENSHOTS !== "1") {
      requireAdminCreds();
      const adminContext = await browser.newContext({ viewport: VIEWPORT });
      const adminPage = await adminContext.newPage();
      try {
        await login(adminPage, ADMIN_EMAIL, ADMIN_PASSWORD);
        await adminPage.goto(`${BASE_URL}/admin/overview`, {
          waitUntil: "domcontentloaded",
        });
        await waitForApp(adminPage);
        await shot(adminPage, "admin-overview");
      } finally {
        await adminContext.close();
      }
    }
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
