import * as dotenv from "dotenv";
dotenv.config();

import { Stagehand } from "@browserbasehq/stagehand";

async function main() {
  const stagehand = new Stagehand({
    env: "LOCAL",
    model: "openai/gpt-4o-mini",
    verbose: 1
  });

  await stagehand.init();

  const page = stagehand.context.pages()[0];
  if (!page) {
    throw new Error("No page found in Stagehand context");
  }

  await page.goto("https://www.google.com");

  const agent = stagehand.agent({
    model: "openai/gpt-4o-mini",
    executionModel: "openai/gpt-4o-mini"
  });

  const result = await agent.execute({
    instruction: "On Google, search for dogs.",
    maxSteps: 10
  });

  console.log(result.message);

  await stagehand.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
