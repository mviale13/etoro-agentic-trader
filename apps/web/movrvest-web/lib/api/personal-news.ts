/**
 * Client for GET /personal-news/{symbol}.
 *
 * A strict mirror of the backend's payload. Every sentence a reader sees
 * is written by the backend and carried here unchanged: this module
 * composes no wording, ranks nothing, scores nothing and never decides
 * whether an article is relevant. The backend's `stated` is the reason,
 * `association_note` is the caveat, and `coverage_notice` is the limit.
 *
 * A failure to reach the backend is `null`, and the section renders
 * nothing rather than an empty inbox — "no items" is a claim the backend
 * makes, not one a fetch error may make on its behalf.
 */

const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export interface PersonalNewsLead {
  providerArticleId: string;
  queriedTicker: string;
  associatedTickers: string[];
  associatedTickerCount: number;
  /** The backend's own caveat about relevance. Never rewritten here. */
  associationNote: string;
  headline: string;
  /** The provider's summary, unchanged. Nothing is generated. */
  providerSummary: string;
  publisherName: string;
  author: string;
  publishedAt: string;
  articleUrl: string;
  /** Massive's classification for this ticker: "positive", "negative" or null. */
  providerSentiment: "positive" | "negative" | null;
  /** The accessible wording for the icon, written by the backend. */
  sentimentLabel: string;
  status: string;
}

export interface PersonalNewsView {
  queriedTicker: string;
  outcome: string;
  /** Why this result is what it is, worded by the backend. */
  stated: string;
  coverageNotice: string;
  /** Whose classification the icons are. Backend-written. */
  sentimentNotice: string;
  retrievedAt: string;
  heading: string;
  explanation: string;
  displayable: boolean;
  leads: PersonalNewsLead[];
}

export async function getPersonalNews(
  symbol: string,
): Promise<PersonalNewsView | null> {
  try {
    const response = await fetch(
      `${BACKEND_URL}/personal-news/${encodeURIComponent(symbol)}`,
      { cache: "no-store" },
    );

    if (!response.ok) {
      return null;
    }

    const payload = await response.json();

    return {
      queriedTicker: String(payload.queried_ticker ?? symbol),
      outcome: String(payload.outcome ?? ""),
      stated: String(payload.stated ?? ""),
      coverageNotice: String(payload.coverage_notice ?? ""),
      sentimentNotice: String(payload.sentiment_notice ?? ""),
      retrievedAt: String(payload.retrieved_at ?? ""),
      heading: String(payload.heading ?? "Ticker News"),
      explanation: String(payload.explanation ?? ""),
      displayable: Boolean(payload.displayable),
      leads: Array.isArray(payload.leads)
        ? payload.leads.map(
            (lead: Record<string, unknown>): PersonalNewsLead => ({
              providerArticleId: String(lead.provider_article_id ?? ""),
              queriedTicker: String(lead.queried_ticker ?? ""),
              associatedTickers: Array.isArray(lead.associated_tickers)
                ? lead.associated_tickers.map(String)
                : [],
              associatedTickerCount: Number(lead.associated_ticker_count ?? 0),
              associationNote: String(lead.association_note ?? ""),
              headline: String(lead.headline ?? ""),
              providerSummary: String(lead.provider_summary ?? ""),
              publisherName: String(lead.publisher_name ?? ""),
              author: String(lead.author ?? ""),
              publishedAt: String(lead.published_at ?? ""),
              articleUrl: String(lead.article_url ?? ""),
              providerSentiment:
                lead.provider_sentiment === "positive" ||
                lead.provider_sentiment === "negative"
                  ? lead.provider_sentiment
                  : null,
              sentimentLabel: String(lead.sentiment_label ?? ""),
              status: String(lead.status ?? ""),
            }),
          )
        : [],
    };
  } catch {
    return null;
  }
}
