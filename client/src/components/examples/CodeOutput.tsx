import CodeOutput from "../CodeOutput";

export default function CodeOutputExample() {
  const sampleCode = `import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod/v3";

const stagehand = new Stagehand({
  env: "LOCAL",
  model: "google/gemini-2.5-flash"
});

await stagehand.init();
const page = stagehand.context.pages()[0];

await page.goto("https://example.com");
await stagehand.act("click the login button");

await stagehand.close();`;

  return (
    <div className="h-96">
      <CodeOutput typescriptCode={sampleCode} />
    </div>
  );
}
