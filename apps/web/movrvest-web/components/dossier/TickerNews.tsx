import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import { getPersonalNews } from "@/lib/api/personal-news";
import type {
  PersonalNewsLead,
  PersonalNewsView,
} from "@/lib/api/personal-news";

/**
 * Ticker News — a display-only discovery surface.
 *
 * Deliberately not called Developments, Verified news, Independent
 * reporting, Material events, Market consensus or News analysis. It is
 * none of those, and the heading is the first place a reader decides
 * what a section means.
 *
 * This component computes nothing. Every sentence — the explanation, the
 * reason a result is empty, the relevance caveat, the sentiment
 * disclosure, the coverage limit — is written by the backend and printed
 * here unchanged. There is no ranking, no sorting, no grouping, no
 * clustering and no counting: the provider's order survives, because
 * reordering by relevance or by sentiment would be an unmeasured
 * judgment made in TypeScript.
 *
 * It is an async server component behind its own Suspense boundary, so a
 * three-request paced read cannot hold up the investment case above it.
 * The dossier renders when the dossier is ready; this arrives when it
 * arrives — once, with no polling and no retry.
 */
export async function TickerNews({ symbol }: { symbol: string }) {
  const news = await getPersonalNews(symbol);

  // A fetch failure is silence, not an empty inbox: "no items" is a
  // claim only the backend may make, and a failed request has not made
  // it. The dossier above is unaffected either way.
  if (!news) {
    return null;
  }

  return <TickerNewsSection news={news} />;
}

/** The quiet placeholder shown while the paced read is in flight. */
export function TickerNewsFallback() {
  return (
    <section className="mt-10 rounded-[28px] border border-slate-200 bg-white px-6 py-7 sm:px-8">
      <h2 className="text-xl font-semibold tracking-[-0.02em] text-slate-950">
        Ticker News
      </h2>
      <p className="mt-2 text-sm text-slate-500">Loading ticker news…</p>
    </section>
  );
}

function TickerNewsSection({ news }: { news: PersonalNewsView }) {
  return (
    <section className="mt-10 rounded-[28px] border border-slate-200 bg-white px-6 py-7 sm:px-8">
      <header>
        <h2 className="text-xl font-semibold tracking-[-0.02em] text-slate-950">
          {news.heading}
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
          {news.explanation}
        </p>
      </header>

      {news.displayable ? (
        // The divider belongs to the list, not to the row: each
        // <details> is the only child of its own <li>, so a `first:`
        // rule on the row matches every row and removes every divider.
        <ol className="mt-6 divide-y divide-slate-100">
          {news.leads.map((lead) => (
            <li key={lead.providerArticleId}>
              <NewsRow lead={lead} />
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-5 text-sm leading-relaxed text-slate-700">
          {news.stated}
        </p>
      )}

      <div className="mt-6 space-y-2 border-t border-slate-100 pt-4">
        {news.displayable ? (
          <p className="text-xs leading-relaxed text-slate-500">
            {news.sentimentNotice}
          </p>
        ) : null}
        <p className="text-xs leading-relaxed text-slate-500">
          {news.coverageNotice}
        </p>
      </div>
    </section>
  );
}

/**
 * One article, as a native disclosure row.
 *
 * `<details>`/`<summary>` rather than a scripted accordion: keyboard
 * operable, screen-reader announced, and expanded by find-in-page
 * without a line of JavaScript.
 */
function NewsRow({ lead }: { lead: PersonalNewsLead }) {
  return (
    <details className="group py-3 [&::-webkit-details-marker]:hidden">
      <summary className="flex cursor-pointer list-none items-start gap-3 rounded-lg px-1 py-1 hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-900">
        <SentimentIcon lead={lead} />

        <span className="min-w-0 flex-1">
          <span className="block text-base font-semibold leading-snug text-slate-950">
            {lead.headline}
          </span>
          <span className="mt-1 block text-xs text-slate-500">
            {lead.publisherName}
            {" · "}
            <time dateTime={lead.publishedAt}>{lead.publishedAt}</time>
          </span>
        </span>

        {/* The expansion indicator. aria-hidden because <details> already
            announces its own expanded state to assistive technology. */}
        <span
          aria-hidden="true"
          className="mt-1 shrink-0 text-slate-400 transition-transform group-open:rotate-90"
        >
          ›
        </span>
      </summary>

      <div className="mt-3 space-y-2 pl-9 pr-1">
        {lead.providerSummary ? (
          <p className="text-sm leading-relaxed text-slate-700">
            {lead.providerSummary}
          </p>
        ) : null}

        {lead.author ? (
          <p className="text-xs text-slate-500">{lead.author}</p>
        ) : null}

        <p className="text-xs text-slate-500">{lead.associationNote}</p>

        <a
          href={lead.articleUrl}
          target="_blank"
          rel="noreferrer noopener"
          className="inline-block text-sm font-semibold text-slate-900 underline underline-offset-4"
        >
          Open publisher article
        </a>
      </div>
    </details>
  );
}

/**
 * Massive's classification, as an icon that says whose it is.
 *
 * Colour supports the arrow and never carries the meaning alone: the
 * direction is in the glyph and the words are in the label the backend
 * wrote. The headline is fully readable with neither. Where there is no
 * classification an empty box keeps the headlines aligned and nothing is
 * announced — an absence is not a neutral verdict.
 */
function SentimentIcon({ lead }: { lead: PersonalNewsLead }) {
  if (lead.providerSentiment === null) {
    return <span aria-hidden="true" className="mt-1 size-4 shrink-0" />;
  }

  const positive = lead.providerSentiment === "positive";
  const Icon = positive ? ArrowUpRight : ArrowDownRight;

  return (
    <span className="mt-1 shrink-0">
      <Icon
        aria-hidden="true"
        className={`size-4 ${positive ? "text-emerald-600" : "text-rose-600"}`}
      />
      <span className="sr-only">{lead.sentimentLabel}</span>
    </span>
  );
}
