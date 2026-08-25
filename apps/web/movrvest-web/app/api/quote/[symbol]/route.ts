import { NextResponse } from "next/server";

const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export const dynamic = "force-dynamic";

/**
 * The Fresh Quote Ribbon's door — the browser calls this app, never a
 * provider.
 *
 * A proxy for the same reason the narrative has one: the backend's
 * address and the provider's credential are server-side facts. The
 * backend owns the one process-wide cache and its single-flight, so
 * however many tabs poll this route, the provider is asked at most once
 * per TTL.
 *
 * A failure returns a typed empty answer at 200: the ribbon is display
 * plumbing, and nothing about a dossier may fail because a quote did.
 */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ symbol: string }> },
) {
  const { symbol } = await params;

  const endpoint = `${BACKEND_URL}/quotes?symbols=${encodeURIComponent(
    symbol.toUpperCase(),
  )}`;

  try {
    const response = await fetch(endpoint, { cache: "no-store" });

    if (!response.ok) {
      return NextResponse.json({ quotes: [] }, { status: 200 });
    }

    return NextResponse.json(await response.json(), { status: 200 });
  } catch {
    return NextResponse.json({ quotes: [] }, { status: 200 });
  }
}
