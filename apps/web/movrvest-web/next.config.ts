import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /**
   * Which hosts may request dev-only assets.
   *
   * **Development only, and it decides whether the app is interactive.**
   * Next blocks cross-origin requests to dev assets, allowing only the
   * hostname the server was started with — `localhost`. `127.0.0.1` is
   * a different origin to it, so opening the app there silently fails
   * to load the dev runtime: the pages render, and nothing hydrates.
   * Every client component is inert, and a toggle that should switch a
   * list in place falls back to being a plain link that reloads the
   * page.
   *
   * It cost an hour to find, because the symptom is a page that looks
   * completely fine. The only clue is one line in the dev server log:
   * "Blocked cross-origin request to Next.js dev resource".
   *
   * Both names are listed because both are used to reach this app —
   * `MOVRVEST_API_URL` defaults to `127.0.0.1`, so that spelling is
   * already in the repo's vocabulary. This has no effect on a
   * production build, which serves no dev assets.
   */
  allowedDevOrigins: ["127.0.0.1", "localhost"],
};

export default nextConfig;
