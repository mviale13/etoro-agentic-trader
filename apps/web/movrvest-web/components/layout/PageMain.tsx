import type { ReactNode } from "react";

/**
 * The one container every page renders its content into.
 *
 * The width is the screen's, not a number chosen in advance. Before
 * this existed the app carried four different answers to the same
 * question — `max-w-[1600px]` on five pages, `w-[90%] max-w-[1700px]`
 * on Research, `max-w-5xl` (1,024px) on a crypto dossier and
 * `max-w-4xl` (896px) on Investor Policy — so the same 1,990px display
 * rendered a token-supply answer in 944px of column and the portfolio
 * beside it in 1,600px. One concept, one implementation.
 *
 * Fluid means gutters, not a percentage. `w-[90%]` grows its own
 * margins with the display, which is why Research rendered *narrower*
 * than the fixed-1,600px pages on a wide screen; constant padding
 * spends every pixel the navigation leaves behind on content.
 *
 * Widening the container cannot turn a paragraph into a
 * 200-character line: prose carries its own reading measure inline —
 * `max-w-2xl` and its siblings appear 16 times in the crypto dossier
 * alone — and those caps are what protect legibility, not the page
 * container.
 *
 * `max-w-[2400px]` is an ultrawide guard rather than a layout width.
 * It engages only past roughly a 2,700px viewport; at 1,440px, 1,990px
 * and 2,560px the container is entirely fluid.
 */
export const PAGE_MAIN_CLASS =
  "mx-auto w-full max-w-[2400px] px-5 py-8 sm:px-8 lg:px-10 lg:py-12 2xl:px-14";

export function PageMain({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <main className={className ? `${PAGE_MAIN_CLASS} ${className}` : PAGE_MAIN_CLASS}>
      {children}
    </main>
  );
}
