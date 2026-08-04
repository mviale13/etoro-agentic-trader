"use client";

import { useEffect } from "react";

import {
  usePageIntegrity,
  type PageIntegrity as PageIntegrityValue,
} from "@/components/system-integrity/PageIntegrityContext";

/**
 * A page's own statement of where its data came from.
 *
 * Render this from a page — including a server component — passing the
 * status derived from the actual fetch result rather than a constant, so a
 * backend that goes down is reported as such.
 *
 * Renders nothing; the floating System Integrity legend displays it.
 */
export function PageIntegrity({
  status,
  endpoint,
  description,
}: PageIntegrityValue) {
  const { declare } = usePageIntegrity();

  useEffect(() => {
    declare({ status, endpoint, description });

    // Clear on navigation, so the next page starts unclassified rather than
    // inheriting a claim that was true of the previous one.
    return () => declare(null);
  }, [declare, status, endpoint, description]);

  return null;
}
