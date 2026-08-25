/**
 * The ribbon's poll loop, extracted from React so its lifecycle is a
 * tested object rather than a hope.
 *
 * Everything a running loop owns — the stopped flag, the pending
 * timer, the AbortController — lives in this closure and dies with
 * `stop()`. Nothing is shared between two loops, which is the whole
 * repair: the previous version kept an `alive` ref *outside* the
 * effect, so a Strict Mode remount could set it true while the first
 * effect's fetch was still in flight, and the zombie would then update
 * state and schedule another timer beside the new loop's own.
 *
 * After `stop()`, this loop:
 * - delivers no quote, however late its in-flight fetch resolves;
 * - advances no clock;
 * - schedules nothing further;
 * and its in-flight request is aborted rather than abandoned.
 *
 * `onTick` fires on every scheduled attempt — visible or not, fetched
 * or failed — because the *render clock* must advance even when no new
 * quote arrives: a current quote expires by that clock, and a loop
 * that only ticked on success would leave "Updated 0 seconds ago"
 * standing through any outage.
 */

import { type FreshQuoteView, parseQuote } from "@/components/quote/quote-model";

export interface QuotePoller {
  /** Poll now if visible — the visibilitychange re-entry. */
  wake(): void;
  stop(): void;
}

export interface QuotePollerOptions {
  fetchQuote: (signal: AbortSignal) => Promise<unknown>;
  onQuote: (quote: FreshQuoteView) => void;
  /** Fired after every attempt, successful or not. The render clock. */
  onTick: () => void;
  intervalMs: number;
  isVisible: () => boolean;
  schedule?: (run: () => void, ms: number) => unknown;
  cancel?: (handle: unknown) => void;
}

export function startQuotePoller(options: QuotePollerOptions): QuotePoller {
  const schedule =
    options.schedule ?? ((run: () => void, ms: number) => setTimeout(run, ms));
  const cancel =
    options.cancel ??
    ((handle: unknown) => clearTimeout(handle as ReturnType<typeof setTimeout>));

  let stopped = false;
  let timer: unknown = null;
  const controller = new AbortController();

  async function attempt(): Promise<void> {
    if (stopped) {
      return;
    }

    if (options.isVisible()) {
      try {
        const body = await options.fetchQuote(controller.signal);

        if (!stopped) {
          const raw =
            typeof body === "object" && body !== null
              ? (body as { quotes?: unknown[] }).quotes?.[0]
              : null;
          const parsed = parseQuote(raw ?? null);

          if (parsed) {
            options.onQuote(parsed);
          }
        }
      } catch {
        // A quote failure is a quote failure. The tick below still
        // advances the render clock, which is what ages a stranded
        // "current" out of its window.
      }
    }

    if (stopped) {
      return;
    }

    options.onTick();
    timer = schedule(run, options.intervalMs);
  }

  function run(): void {
    void attempt();
  }

  run();

  return {
    wake(): void {
      if (stopped || !options.isVisible()) {
        return;
      }

      if (timer !== null) {
        cancel(timer);
        timer = null;
      }

      run();
    },
    stop(): void {
      stopped = true;
      controller.abort();

      if (timer !== null) {
        cancel(timer);
        timer = null;
      }
    },
  };
}
