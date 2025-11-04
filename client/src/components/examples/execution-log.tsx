import { ExecutionLog } from "../execution-log";

export default function ExecutionLogExample() {
  const logs = [
    { timestamp: "10:23:45", level: "info" as const, message: "Starting automation task..." },
    { timestamp: "10:23:46", level: "success" as const, message: "Successfully loaded page: https://linkedin.com" },
    { timestamp: "10:23:47", level: "loading" as const, message: "Searching for element: #search-input" },
    { timestamp: "10:23:48", level: "success" as const, message: "Element found, typing search query" },
    { timestamp: "10:23:49", level: "info" as const, message: "Waiting for search results to load..." },
    { timestamp: "10:23:51", level: "error" as const, message: "Timeout: Search results did not load within 5 seconds" },
  ];

  return (
    <div className="h-96 border rounded-lg">
      <ExecutionLog logs={logs} />
    </div>
  );
}
