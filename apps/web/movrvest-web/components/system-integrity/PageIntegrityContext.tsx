"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { BackendStatus } from "@/components/system-integrity/BackendStatusDot";

export type PageIntegrity = {
  status: BackendStatus;
  /** Where the data came from, e.g. "/executive/portfolio". */
  endpoint?: string;
  description: string;
};

type IntegrityContextValue = {
  integrity: PageIntegrity | null;
  declare: (integrity: PageIntegrity | null) => void;
};

const PageIntegrityContext = createContext<IntegrityContextValue | null>(null);

/**
 * Holds the data provenance the current page declared about itself.
 *
 * The previous implementation kept a hardcoded route map, which drifted out
 * of date the moment a page changed and ended up asserting the opposite of
 * the truth. A page knows its own data source; nothing else reliably does.
 */
export function PageIntegrityProvider({ children }: { children: ReactNode }) {
  const [integrity, setIntegrity] = useState<PageIntegrity | null>(null);

  const declare = useCallback((next: PageIntegrity | null) => {
    setIntegrity(next);
  }, []);

  const value = useMemo(
    () => ({ integrity, declare }),
    [integrity, declare],
  );

  return (
    <PageIntegrityContext.Provider value={value}>
      {children}
    </PageIntegrityContext.Provider>
  );
}

export function usePageIntegrity(): IntegrityContextValue {
  const context = useContext(PageIntegrityContext);

  if (context === null) {
    throw new Error(
      "usePageIntegrity must be used inside a PageIntegrityProvider.",
    );
  }

  return context;
}
