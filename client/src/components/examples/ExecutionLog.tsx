import ExecutionLog, { LogEntry } from "../ExecutionLog";

export default function ExecutionLogExample() {
  const sampleEntries: LogEntry[] = [
    {
      id: "1",
      timestamp: Date.now() - 5000,
      action: "Navigate to URL",
      status: "success",
      description: "Loaded https://example.com",
    },
    {
      id: "2",
      timestamp: Date.now() - 3000,
      action: "Observe elements",
      status: "success",
      selector: "xpath=/html/body/div[1]/button[1]",
      description: "Found login button",
    },
    {
      id: "3",
      timestamp: Date.now() - 1000,
      action: "Click element",
      status: "running",
      selector: "xpath=/html/body/div[1]/button[1]",
      description: "Clicking login button",
    },
  ];

  return (
    <div className="h-96">
      <ExecutionLog entries={sampleEntries} />
    </div>
  );
}
