import { NextResponse } from "next/server";

const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export const dynamic = "force-dynamic";

/**
 * The written case, fetched from the browser after the page is read.
 *
 * A proxy rather than a direct call because the backend's address is a
 * server-side setting: publishing it so a browser could reach it would
 * put the platform's own API on the public side of the app for the sake
 * of one paragraph.
 *
 * The dossier does not wait for this. Its evidence is ready in under two
 * seconds and the wording takes fifteen to twenty, all of it one model
 * call, so the case is served decided and the prose arrives when it is
 * written.
 */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ symbol: string }> },
) {
  const { symbol } = await params;

  const endpoint = `${BACKEND_URL}/executive/${encodeURIComponent(
    symbol.toUpperCase(),
  )}/narrative`;

  try {
    const response = await fetch(endpoint, { cache: "no-store" });

    if (!response.ok) {
      return NextResponse.json(
        {
          narrative: null,
          narrative_absent: `The narrative could not be requested (${response.status}).`,
        },
        { status: 200 },
      );
    }

    return NextResponse.json(await response.json());
  } catch {
    // An unreachable backend costs the wording, never the case: the
    // dossier is already on screen and canonical without it.
    return NextResponse.json(
      {
        narrative: null,
        narrative_absent:
          "The narrative could not be requested, so the case stands as measured.",
      },
      { status: 200 },
    );
  }
}
