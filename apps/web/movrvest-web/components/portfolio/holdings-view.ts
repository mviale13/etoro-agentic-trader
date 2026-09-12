/**
 * Which of the two holdings views the URL asks for.
 *
 * Its own module because both sides read it: the server component
 * decides the first render from `?holdings=`, and the client table
 * re-reads it when the toggle or the Back button changes the URL. A
 * `"use client"` file cannot serve the first of those — every export
 * of one is a client reference, and calling it during the server
 * render throws.
 */

export const HOLDINGS_VIEWS = ["securities", "trades"] as const;

export type HoldingsView = (typeof HOLDINGS_VIEWS)[number];

export const HOLDINGS_PARAM = "holdings";

/**
 * The view named in the URL, defaulting to **securities**.
 *
 * "What the account holds" is a question about securities; the broker's
 * trade rows are the evidence behind the answer rather than the answer.
 * Anything unrecognised is the default rather than an error — a URL is
 * typed by hand and a bad one should still render the page.
 */
export function holdingsViewFromParam(
  param: string | string[] | undefined | null,
): HoldingsView {
  const value = Array.isArray(param) ? param[0] : param;

  return value === "trades" ? "trades" : "securities";
}

/** Where a view lives, so the toggle and the page agree on one answer. */
export function holdingsViewHref(view: HoldingsView): string {
  return view === "securities"
    ? "/portfolio"
    : `/portfolio?${HOLDINGS_PARAM}=${view}`;
}
