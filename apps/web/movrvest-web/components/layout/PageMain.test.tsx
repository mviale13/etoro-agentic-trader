import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { PAGE_MAIN_CLASS, PageMain } from "./PageMain";

/**
 * The container is one implementation of one concept, and it is fluid.
 *
 * Both halves need pinning. A render test alone would pass while a page
 * quietly went back to declaring its own `<main className="…max-w-5xl">`
 * — which is exactly the state this replaced, four different answers to
 * the width question across nine containers.
 */

const WEB = join(__dirname, "..", "..");

/**
 * Both trees, because a container hid in the second one.
 *
 * `WorkspacePlaceholder` — a component, not a page — carried a tenth
 * `<main className="…max-w-6xl">` that a walk over `app/` alone could
 * not see, and Brain and Settings rendered through it. A guard that
 * only watches where the last stray was found is not a guard.
 */
function pageSources(): { file: string; source: string }[] {
  const found: { file: string; source: string }[] = [];

  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(path);
      } else if (entry.name.endsWith(".tsx")) {
        found.push({ file: path, source: readFileSync(path, "utf8") });
      }
    }
  };

  for (const tree of ["app", "components"]) {
    walk(join(WEB, tree));
  }

  // The container itself is the one place a `<main>` may be written,
  // and a test file quotes both spellings while asserting on them.
  return found.filter(
    ({ file }) =>
      !file.endsWith("PageMain.tsx") && !file.endsWith(".test.tsx"),
  );
}

describe("PageMain", () => {
  it("renders a main element carrying the shared container", () => {
    const html = renderToStaticMarkup(<PageMain>content</PageMain>);

    expect(html).toContain("<main");
    expect(html).toContain(PAGE_MAIN_CLASS);
  });

  it("appends a page's own classes without dropping the container", () => {
    const html = renderToStaticMarkup(
      <PageMain className="pb-24">content</PageMain>,
    );

    expect(html).toContain(PAGE_MAIN_CLASS);
    expect(html).toContain("pb-24");
  });

  it("is fluid: the width tracks the display, not a chosen number", () => {
    expect(PAGE_MAIN_CLASS).toContain("w-full");

    // `w-[90%]` grows its own margins with the display, which made
    // Research render *narrower* than the fixed-1,600px pages on a wide
    // screen. Gutters are constant; the content takes the rest.
    expect(PAGE_MAIN_CLASS).not.toMatch(/w-\[\d+%\]/);

    // The only max-width permitted is the ultrawide guard, which must
    // stay clear of real displays — a 2,560px monitor is still fluid.
    const caps = [...PAGE_MAIN_CLASS.matchAll(/max-w-\[(\d+)px\]/g)].map((m) =>
      Number(m[1]),
    );
    expect(caps).toHaveLength(1);
    expect(caps[0]).toBeGreaterThanOrEqual(2400);
    expect(PAGE_MAIN_CLASS).not.toMatch(/max-w-(?:\d?xl|screen-\w+)\b/);
  });

  it("is the only page container: no page declares its own width", () => {
    const offenders = pageSources()
      .filter(({ source }) => /<main[\s>]/.test(source))
      .map(({ file }) => file);

    expect(offenders).toEqual([]);
  });

  it("covers every page that renders one", () => {
    const users = pageSources().filter(({ source }) =>
      source.includes("<PageMain"),
    );

    // Ten containers across nine files when this was written; the
    // guard is that pages use it at all, so it may only grow.
    expect(users.length).toBeGreaterThanOrEqual(9);

    for (const { file, source } of users) {
      expect(
        source.includes('from "@/components/layout/PageMain"'),
        `${file} renders PageMain without importing it`,
      ).toBe(true);
    }
  });
});
