import { ExecutiveBrief } from "@/components/brief/ExecutiveBrief";
import { microsoftExecutiveBrief } from "@/mocks/executive-brief";

export default function BriefPage() {
  // A fixed Microsoft example, not the investor's holdings.
  return (
    <ExecutiveBrief brief={microsoftExecutiveBrief} status="placeholder" />
  );
}
