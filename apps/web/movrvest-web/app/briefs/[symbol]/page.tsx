import { ExecutiveBrief } from "@/components/brief/ExecutiveBrief";
import { microsoftExecutiveBrief } from "@/mocks/executive-brief";
import { PageIntegrity } from "@/components/system-integrity/PageIntegrity";

export default function BriefPage() {
  // A fixed Microsoft example, not the investor's holdings.
  return (
    <>
      <PageIntegrity
        status="placeholder"
        description="This brief renders a fixed Microsoft example, not your holdings."
      />

      <ExecutiveBrief brief={microsoftExecutiveBrief} status="placeholder" />
    </>
  );
}
