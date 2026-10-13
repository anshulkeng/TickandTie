import type { Metadata } from "next";

import { LegalPage } from "@/components/LegalPage";
import { lastUpdated, terms, updatedLabel } from "@/content/legal";

export const metadata: Metadata = { title: "Terms | Tick & Tie" };

export default function Terms() {
  return <LegalPage {...terms} updatedLabel={updatedLabel} updated={lastUpdated} />;
}