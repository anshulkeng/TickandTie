import type { Metadata } from "next";

import { LegalPage } from "@/components/LegalPage";
import { lastUpdated, privacy, updatedLabel } from "@/content/legal";

export const metadata: Metadata = { title: "Privacy | Tick & Tie" };

export default function Privacy() {
  return <LegalPage {...privacy} updatedLabel={updatedLabel} updated={lastUpdated} />;
}