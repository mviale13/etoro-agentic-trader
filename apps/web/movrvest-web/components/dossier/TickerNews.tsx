import type { PersonalNewsView } from "@/lib/api/personal-news";

/**
 * Ticker News — a display-only discovery surface.
 *
 * It is deliberately not called Developments, Verified news, Independent
 * reporting, Material events, Market consensus or News analysis. It is
 * none of those, and the heading is the first place a reader decides
 * what a section means.
 *
 * This component computes nothing. Every sentence — the explanation, the
 * reason a result is empty, the relevance caveat, the coverage limit —
 * is written by the backend and printed here unchanged. There is no
 * ranking, no sorting, no grouping, no clustering, no sentiment and no
 * badge: the provider's order survives, because reordering by anything
 * would be an unmeasured judgment about relevance.
 */
export function TickerNews({ news }: { news: PersonalNewsView | null }) {
  // A fetch failure is silence, not an empty inbox: "no items" is a
  // claim only the backend may make.
  if (!news) {
    return null;
  }

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
        <ol className="mt-6 space-y-5">
          {news.leads.map((lead) => (
            <li
              key={lead.providerArticleId}
              className="border-t border-slate-100 pt-5 first:border-t-0 first:pt-0"
            >
              <h3 className="text-base font-semibold leading-snug text-slate-950">
                {lead.headline}
              </h3>

              <p className="mt-1 text-xs text-slate-500">
                {lead.publisherName}
                {lead.author ? ` · ${lead.author}` : ""}
                {" · "}
                <time dateTime={lead.publishedAt}>{lead.publishedAt}</time>
              </p>

              {lead.providerSummary ? (
                <p className="mt-2 text-sm leading-relaxed text-slate-700">
                  {lead.providerSummary}
                </p>
              ) : null}

              <p className="mt-2 text-xs text-slate-500">
                {lead.associationNote}
              </p>

              <a
                href={lead.articleUrl}
                target="_blank"
                rel="noreferrer noopener"
                className="mt-2 inline-block text-sm font-semibold text-slate-900 underline underline-offset-4"
              >
                Open publisher article
              </a>
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-5 text-sm leading-relaxed text-slate-700">
          {news.stated}
        </p>
      )}

      <p className="mt-6 border-t border-slate-100 pt-4 text-xs leading-relaxed text-slate-500">
        {news.coverageNotice}
      </p>
    </section>
  );
}
