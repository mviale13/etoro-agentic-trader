import { CalendarClock } from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { WorkspacePlaceholder } from "@/components/workspace/WorkspacePlaceholder";

type EventPageProps = {
  params: Promise<{ slug: string }>;
};

function titleFromSlug(slug: string) {
  return slug
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export default async function EventPage({ params }: EventPageProps) {
  const { slug } = await params;

  return (
    <DashboardLayout>
      <WorkspacePlaceholder
        eyebrow="Important event"
        title={titleFromSlug(slug)}
        question="Why does this event matter for my portfolio?"
        description="This event workspace will connect timing, affected holdings, market expectations, scenarios, risks, and the decisions that may be required."
        icon={CalendarClock}
        nextHref="/markets"
        nextLabel="Review market intelligence"
      />
    </DashboardLayout>
  );
}
