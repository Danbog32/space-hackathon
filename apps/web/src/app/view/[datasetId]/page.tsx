"use client";

import { ViewerContainer } from "@/components/ViewerContainer";

export default function ViewPage({ params }: { params: { datasetId: string } }) {
  return <ViewerContainer datasetId={params.datasetId} />;
}
