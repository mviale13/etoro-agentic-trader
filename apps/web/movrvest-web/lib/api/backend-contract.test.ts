/**
 * Every server-side backend reader uses the canonical contract.
 *
 * `MOVRVEST_API_URL` is the one name that points this app at its
 * backend. `cycle-review.ts` read `BACKEND_URL` while ten sibling
 * modules read the canonical name, so redirecting the app moved every
 * page except the homepage — a split that cost real time during #230
 * and that this scan makes structurally unrepeatable: a new module
 * reading a non-canonical name fails here, not in production.
 */

import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const WEB_ROOT = join(__dirname, "..", "..");

/** Every module that resolves the backend's address at module scope. */
function backendReaders(): string[] {
  const apiDir = join(WEB_ROOT, "lib", "api");

  const readers = readdirSync(apiDir)
    .filter((name) => name.endsWith(".ts") && !name.endsWith(".test.ts"))
    .map((name) => join(apiDir, name));

  readers.push(join(WEB_ROOT, "lib", "strategy-api.ts"));
  readers.push(join(WEB_ROOT, "app", "api", "narrative", "[symbol]", "route.ts"));

  return readers.filter((path) => readFileSync(path, "utf8").includes("8000"));
}

describe("the canonical backend contract", () => {
  it("finds the readers it exists to police", () => {
    // The scan is only a guard while it actually sees the modules; an
    // empty list would pass every assertion below by vacuity.
    expect(backendReaders().length).toBeGreaterThanOrEqual(10);
  });

  it("every reader resolves the backend from MOVRVEST_API_URL", () => {
    for (const path of backendReaders()) {
      expect(readFileSync(path, "utf8"), path).toContain(
        "process.env.MOVRVEST_API_URL",
      );
    }
  });

  it("no reader resolves the backend from a non-canonical name", () => {
    for (const path of backendReaders()) {
      expect(readFileSync(path, "utf8"), path).not.toContain(
        "process.env.BACKEND_URL",
      );
    }
  });
});
