import { describe, expect, it } from "vitest";

import { headlineModel, ribbonModel } from "./quote-model";
import { startQuotePoller } from "./quote-poller";

/**
 * The poll loop's lifecycle, pinned without React: the loop is a plain
 * object, so a mount/cleanup/remount is three function calls and a
 * zombie is directly observable rather than inferred from flaky state.
 */

function wireQuote(overrides: Record<string, unknown> = {}) {
  return {
    movrvest_symbol: "HYPE",
    asset_class: "crypto",
    provider: "eToro",
    provider_instrument_identity: "100446",
    provider_label: "Hyperliquid",
    price: 80.86,
    currency: null,
    bid: 80.86,
    ask: 80.87,
    source_as_of: "2026-08-25T14:15:53.343213+00:00",
    received_at: "2026-08-25T14:15:53.5+00:00",
    clock_kind: "source_stated",
    delay_status: "unknown",
    market_status: "unknown",
    status: "current",
    stated: "As eToro stated it, on the source's own clock.",
    ...overrides,
  };
}

/** A hand-cranked scheduler: nothing fires until the test fires it. */
function scheduler() {
  const pending: (() => void)[] = [];

  return {
    schedule: (run: () => void) => {
      pending.push(run);

      return run;
    },
    cancel: (handle: unknown) => {
      const index = pending.indexOf(handle as () => void);

      if (index >= 0) {
        pending.splice(index, 1);
      }
    },
    fire: async () => {
      const run = pending.shift();

      run?.();
      // Let the attempt's promise chain settle.
      await new Promise((resolve) => setTimeout(resolve, 0));
    },
    pending,
  };
}

function harness(options: {
  answers: (unknown | Error)[];
  visible?: () => boolean;
}) {
  const clock = scheduler();
  const quotes: unknown[] = [];
  const ticks: number[] = [];
  let calls = 0;

  const poller = startQuotePoller({
    fetchQuote: async () => {
      const answer = options.answers[Math.min(calls, options.answers.length - 1)];

      calls += 1;

      if (answer instanceof Error) {
        throw answer;
      }

      return answer;
    },
    onQuote: (quote) => quotes.push(quote),
    onTick: () => ticks.push(Date.now()),
    intervalMs: 60_000,
    isVisible: options.visible ?? (() => true),
    schedule: clock.schedule,
    cancel: clock.cancel,
  });

  return {
    poller,
    clock,
    quotes,
    ticks,
    fetches: () => calls,
    settle: () => new Promise((resolve) => setTimeout(resolve, 0)),
  };
}

describe("the poll loop", () => {
  it("delivers a quote, ticks, and schedules the next attempt", async () => {
    const h = harness({ answers: [{ quotes: [wireQuote()] }] });

    await h.settle();

    expect(h.quotes).toHaveLength(1);
    expect(h.ticks).toHaveLength(1);
    expect(h.clock.pending).toHaveLength(1);

    h.poller.stop();
  });

  it("ticks on a failed poll — the render clock advances through outages", async () => {
    const h = harness({
      answers: [{ quotes: [wireQuote()] }, new Error("connection refused")],
    });

    await h.settle(); // success
    await h.clock.fire(); // failure

    expect(h.quotes).toHaveLength(1); // no second quote
    expect(h.ticks).toHaveLength(2); // but the clock ticked anyway

    h.poller.stop();
  });

  it("a current quote crosses 120 seconds of failures and stops presenting as current", async () => {
    // The ruled pin, end to end: one success, then transport failures
    // only. The loop keeps ticking; the model, asked at each tick's
    // clock, drops the claim once the source age passes the window —
    // with no successful response required.
    const h = harness({
      answers: [{ quotes: [wireQuote()] }, new Error("down")],
    });

    await h.settle();

    const held = h.quotes[0] as Parameters<typeof ribbonModel>[0];

    // Two failed polls later the render clock has moved 121 seconds
    // past the source moment.
    await h.clock.fire();
    await h.clock.fire();

    expect(h.ticks).toHaveLength(3);
    expect(h.quotes).toHaveLength(1);

    const at121 = new Date("2026-08-25T14:17:54.4Z");

    expect(ribbonModel(held, at121)?.current).toBe(false);
    expect(ribbonModel(held, at121)?.attribution).toContain("As of");
    expect(
      headlineModel(held, { stated: "$79.14", age: "22 hours ago" }, at121).kind,
    ).toBe("established");

    h.poller.stop();
  });

  it("a stopped loop delivers nothing, however late its fetch resolves", async () => {
    let release: (value: unknown) => void = () => {};
    const quotes: unknown[] = [];
    const ticks: number[] = [];
    const clock = scheduler();

    const poller = startQuotePoller({
      fetchQuote: () => new Promise((resolve) => (release = resolve)),
      onQuote: (quote) => quotes.push(quote),
      onTick: () => ticks.push(Date.now()),
      intervalMs: 60_000,
      isVisible: () => true,
      schedule: clock.schedule,
      cancel: clock.cancel,
    });

    // Stop while the first fetch is still in flight, then let it
    // resolve successfully.
    poller.stop();
    release({ quotes: [wireQuote()] });
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(quotes).toHaveLength(0); // no state update
    expect(ticks).toHaveLength(0); // no clock advance
    expect(clock.pending).toHaveLength(0); // no timer scheduled
  });

  it("survives a Strict Mode mount, cleanup and remount with one live loop", async () => {
    // React Strict Mode runs the effect, cleans it up, and runs it
    // again. The first loop must be absolutely dead — the shared-ref
    // version allowed the remount to revive it, and two loops then
    // polled side by side.
    let releaseFirst: (value: unknown) => void = () => {};
    const clock = scheduler();
    const quotes: unknown[] = [];
    const ticks: number[] = [];

    const mount = (
      fetchQuote: () => Promise<unknown>,
    ): ReturnType<typeof startQuotePoller> =>
      startQuotePoller({
        fetchQuote,
        onQuote: (quote) => quotes.push(quote),
        onTick: () => ticks.push(Date.now()),
        intervalMs: 60_000,
        isVisible: () => true,
        schedule: clock.schedule,
        cancel: clock.cancel,
      });

    // Mount 1: fetch hangs. Cleanup before it resolves.
    const first = mount(() => new Promise((resolve) => (releaseFirst = resolve)));

    first.stop();

    // Mount 2: answers immediately.
    const second = mount(async () => ({ quotes: [wireQuote()] }));

    await new Promise((resolve) => setTimeout(resolve, 0));

    // The zombie's fetch now resolves, late.
    releaseFirst({ quotes: [wireQuote({ price: 999999 })] });
    await new Promise((resolve) => setTimeout(resolve, 0));

    // Exactly one quote — the live loop's — and exactly one scheduled
    // timer. The zombie delivered nothing and scheduled nothing.
    expect(quotes).toHaveLength(1);
    expect((quotes[0] as { price: number }).price).toBe(80.86);
    expect(ticks).toHaveLength(1);
    expect(clock.pending).toHaveLength(1);

    second.stop();

    expect(clock.pending).toHaveLength(0);
  });

  it("aborts the in-flight request on stop", async () => {
    let seen: AbortSignal | null = null;

    const poller = startQuotePoller({
      fetchQuote: (signal) => {
        seen = signal;

        return new Promise(() => {});
      },
      onQuote: () => {},
      onTick: () => {},
      intervalMs: 60_000,
      isVisible: () => true,
      schedule: () => null,
      cancel: () => {},
    });

    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(seen).not.toBeNull();
    expect(seen!.aborted).toBe(false);

    poller.stop();

    expect(seen!.aborted).toBe(true);
  });

  it("fetches nothing while hidden, and still ticks", async () => {
    const h = harness({
      answers: [{ quotes: [wireQuote()] }],
      visible: () => false,
    });

    await h.settle();

    expect(h.fetches()).toBe(0);
    expect(h.quotes).toHaveLength(0);
    expect(h.ticks).toHaveLength(1);
    expect(h.clock.pending).toHaveLength(1);

    h.poller.stop();
  });

  it("wake polls immediately when visible and never after stop", async () => {
    let visible = false;
    const h = harness({
      answers: [{ quotes: [wireQuote()] }],
      visible: () => visible,
    });

    await h.settle();

    expect(h.fetches()).toBe(0);

    visible = true;
    h.poller.wake();
    await h.settle();

    expect(h.fetches()).toBe(1);
    expect(h.quotes).toHaveLength(1);

    h.poller.stop();
    h.poller.wake();
    await h.settle();

    expect(h.fetches()).toBe(1);
  });
});
