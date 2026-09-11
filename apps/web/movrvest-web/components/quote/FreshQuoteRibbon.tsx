"use client";

/**
 * The Fresh Quote Ribbon — a display-only price in the hero, on the
 * provider's own clock.
 *
 * A client component because freshness is a client concern: it polls
 * this app's own `/api/quote/…` proxy (never a provider) once a minute,
 * and only while the page is visible — a hidden tab asks for nothing.
 * The backend owns the process-wide cache and single-flight, so
 * however many tabs poll, the provider is asked at most once per TTL.
 *
 * It renders nothing decisive. No decision, course, envelope or score
 * reads it; a fetch failure leaves the fallback exactly as the server
 * rendered it; and the wording comes from the model module, which never
 * says "live".
 */

import { useEffect, useState } from "react";

import {
  type FreshQuoteView,
  type StoredPrice,
  headlineModel,
  ribbonModel,
} from "@/components/quote/quote-model";
import { startQuotePoller } from "@/components/quote/quote-poller";

const POLL_MS = 60_000;

/**
 * One quote and one render clock, owned by an effect-local poller.
 *
 * The clock advances on every scheduled attempt — including failed ones
 * — because presentation currency expires by it: after 120 seconds
 * without a newer quote, the model stops calling the held quote current
 * whether or not the backend ever answered again.
 *
 * Everything the loop owns lives inside the poller `startQuotePoller`
 * returns, and `stop()` in the cleanup ends it absolutely: a Strict
 * Mode mount/cleanup/remount leaves exactly one live loop, and a
 * stopped loop's in-flight fetch can neither set state nor schedule.
 */
function useFreshQuote(symbol: string): {
  quote: FreshQuoteView | null;
  renderClock: Date;
} {
  const [quote, setQuote] = useState<FreshQuoteView | null>(null);
  const [renderClock, setRenderClock] = useState<Date>(() => new Date());

  useEffect(() => {
    const poller = startQuotePoller({
      fetchQuote: async (signal) => {
        const response = await fetch(
          `/api/quote/${encodeURIComponent(symbol)}`,
          { cache: "no-store", signal },
        );

        return response.ok ? response.json() : null;
      },
      onQuote: setQuote,
      onTick: () => setRenderClock(new Date()),
      intervalMs: POLL_MS,
      isVisible: () => document.visibilityState === "visible",
    });

    function onVisible(): void {
      poller.wake();
    }

    document.addEventListener("visibilitychange", onVisible);

    return () => {
      document.removeEventListener("visibilitychange", onVisible);
      poller.stop();
    };
  }, [symbol]);

  return { quote, renderClock };
}

/**
 * The stock hero's ribbon: the fresh figure where one stands, its
 * honest "as of" where it is stale, and nothing at all otherwise —
 * which is exactly what the hero showed before this existed.
 */
export function StockQuoteRibbon({ symbol }: { symbol: string }) {
  const { quote, renderClock } = useFreshQuote(symbol);
  const model = ribbonModel(quote, renderClock);

  if (!model) {
    return null;
  }

  return (
    <div className="text-right">
      <p className="text-3xl font-semibold tabular-nums text-slate-950">
        {model.figure}
      </p>

      <p className="mt-1 text-xs text-slate-500" title={quote?.stated}>
        {model.attribution}
      </p>

      {model.qualifiers.map((qualifier) => (
        <p key={qualifier} className="mt-0.5 text-xs text-slate-500">
          {qualifier}
        </p>
      ))}
    </div>
  );
}

/**
 * The crypto hero's headline price.
 *
 * Server-rendered with the stored fallback, so the page never waits on
 * a quote; the first successful poll replaces it with the fresh figure
 * — one visible update, no refresh. The stored price and its
 * methodology remain under Evidence untouched; this only decides which
 * figure leads.
 *
 * **It takes the whole stored row, not the figure off it.** Passing the
 * value alone is what collapsed a source conflict into an absence: a
 * conflicted row's figure is null by construction, so the value on its
 * own is the same null an empty store sends, and the hero reported
 * "Price unavailable." for a price its sources had each reported and
 * disagreed about. The states are the row's to distinguish, so the row
 * is what arrives here — standing included, because the label a stored
 * figure gets is the standing's to choose.
 */
export function CryptoHeadlinePrice({
  symbol,
  stored,
}: {
  symbol: string;
  stored: StoredPrice | null;
}) {
  const { quote, renderClock } = useFreshQuote(symbol);

  return (
    <CryptoHeadlinePriceView quote={quote} stored={stored} now={renderClock} />
  );
}

/**
 * The headline itself, given a quote and a stored row — no polling, no
 * state, no clock of its own.
 *
 * Split out so the precedence is **render-testable at every input**.
 * `CryptoHeadlinePrice` gets its quote from an effect, and effects do
 * not run under `renderToStaticMarkup`, so through that component the
 * quote is permanently null and the one case that matters most —
 * *a current quote arriving beside a conflicted stored row* — could not
 * be rendered at all. It can be rendered here.
 */
export function CryptoHeadlinePriceView({
  quote,
  stored,
  now,
}: {
  quote: FreshQuoteView | null;
  stored: StoredPrice | null;
  now: Date;
}) {
  const model = headlineModel(quote, stored, now);

  // Sources disagree, and that is a finding rather than a gap — and it
  // is checked first, ahead of the quote. The standing is the gate's
  // own label and the sentence beneath it is the gate's own account of
  // the disagreement, rendered character for character: nothing here
  // shortens it, names the sources out of it or chooses between them.
  // No figure is rendered at any size, from any source. The Evidence
  // view's rule is that a conflict is never hidden behind a value, and
  // a display quote is one more vendor's value, not a ruling on the
  // disagreement.
  if (model.kind === "conflicted") {
    return (
      <div className="max-w-sm text-right">
        <p className="text-xl font-semibold text-slate-900">
          {model.storedStandingStated}
        </p>

        {model.conflictBecause ? (
          <p className="mt-1 text-left text-xs leading-5 text-slate-500">
            {model.conflictBecause}
          </p>
        ) : null}
      </div>
    );
  }

  if (model.kind === "fresh" && model.ribbon) {
    return (
      <div className="text-right">
        <p className="text-3xl font-semibold tabular-nums text-slate-950">
          {model.ribbon.figure}
        </p>

        <p className="mt-1 text-xs text-slate-500" title={quote?.stated}>
          {model.ribbon.attribution}
        </p>

        {model.ribbon.qualifiers.map((qualifier) => (
          <p key={qualifier} className="mt-0.5 text-xs text-slate-500">
            {qualifier}
          </p>
        ))}
      </div>
    );
  }

  // The stored figure under its own standing. "Last established price"
  // is this platform's framing of a *corroborated* stored reading — the
  // "last" separates it from a live quote — and it was printed over a
  // single-vendor claim too, which let the weaker claim borrow the
  // stronger's authority in the one place a reader looks first. A claim
  // now carries the gate's own words for what it is.
  if (model.kind === "established" || model.kind === "claimed") {
    return (
      <div className="text-right">
        <p className="text-3xl font-semibold tabular-nums text-slate-950">
          {model.storedStated}
        </p>

        <p className="mt-1 text-xs text-slate-500">
          {model.kind === "established"
            ? "Last established price"
            : model.storedStandingStated}
          {model.storedAge ? ` · ${model.storedAge}` : ""}
        </p>
      </div>
    );
  }

  // Nothing is held, and nothing is claimed about why — the investor
  // needs the state, not an account of this platform's store.
  return (
    <div className="text-right">
      <p className="text-sm text-slate-500">Price unavailable.</p>
    </div>
  );
}
