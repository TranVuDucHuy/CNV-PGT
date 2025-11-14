// ContentPane.tsx
"use client";

import React, { useEffect, useState } from "react";
import { useViewHandle } from "../view/viewHandle";
import useResultHandle from "../result/resultHandle";
import SampleBinTable from "./viewpanes/SampleBinTable";
import { SampleBin } from "@/types/result";

export default function ContentPane() {
  const { checked } = useViewHandle();
  const { resultDtos } = useResultHandle();

  const [bins, setBins] = useState<SampleBin[]>([]);

  useEffect(() => {
    const newBins = resultDtos?.[0]?.bins ?? [];
    setBins(newBins);
  }, [resultDtos]);

  return (
    <details>
      {checked.bin ? (
        <div>
          <SampleBinTable data={bins} />
        </div>
      ) : (
        <div>
            Chưa có gì hết
        </div>
      )}
    </details>
  );
}
