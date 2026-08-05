"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BriefcaseBusiness,
  ChartNoAxesCombined,
  FlaskConical,
  History,
  LayoutDashboard,
  ScrollText,
  Settings,
} from "lucide-react";

/**
 * The investor's map of the product, not the system's map of itself.
 *
 * Internal concepts — the Brain, committees, evidence stores — are not
 * primary navigation. They are exposed inside investment cases through
 * progressive disclosure; `/brain` remains reachable as a diagnostics
 * route without being advertised here.
 */
const navigation = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/portfolio", label: "Portfolio", icon: BriefcaseBusiness },
  { href: "/research", label: "Research", icon: FlaskConical },
  { href: "/markets", label: "Markets", icon: ChartNoAxesCombined },
  { href: "/track-record", label: "Track Record", icon: History },
  { href: "/strategy", label: "Investor Policy", icon: ScrollText },
  { href: "/settings", label: "Settings", icon: Settings },
];

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function ExecutiveNavigation() {
  const pathname = usePathname();

  return (
    <aside className="border-b border-slate-200 bg-slate-950 text-slate-100 lg:fixed lg:inset-y-0 lg:left-0 lg:w-64 lg:border-b-0 lg:border-r lg:border-slate-800">
      <div className="flex h-full flex-col px-4 py-4 lg:px-5 lg:py-8">
        <Link href="/" className="block px-2">
          <p className="text-lg font-semibold tracking-tight">MOVRvest</p>
          <p className="mt-1 text-xs text-slate-400">
            Artificial Chief Investment Officer
          </p>
        </Link>

        <nav className="mt-4 flex gap-2 overflow-x-auto pb-1 lg:mt-10 lg:flex-col lg:overflow-visible lg:pb-0">
          {navigation.map(({ href, label, icon: Icon }) => {
            const active = isActive(pathname, href);

            return (
              <Link
                key={href}
                href={href}
                className={`flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                  active
                    ? "bg-white text-slate-950"
                    : "text-slate-400 hover:bg-slate-900 hover:text-white"
                }`}
              >
                <Icon aria-hidden="true" className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </nav>

        <p className="mt-auto hidden px-3 pt-8 text-xs leading-5 text-slate-500 lg:block">
          Intelligence becomes conviction.
        </p>
      </div>
    </aside>
  );
}
