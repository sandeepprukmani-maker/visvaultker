import { ExecutionStatus } from '../ExecutionStatus';

const mockSteps = [
  {
    id: "1",
    action: "Navigate to https://example.com",
    status: "completed" as const,
    duration: "1.2s",
    timestamp: "10:23:45 AM",
  },
  {
    id: "2",
    action: "Wait for page load",
    status: "completed" as const,
    duration: "0.8s",
    timestamp: "10:23:46 AM",
  },
  {
    id: "3",
    action: "Click 'Login' button",
    status: "running" as const,
    timestamp: "10:23:47 AM",
  },
  {
    id: "4",
    action: "Fill username field",
    status: "pending" as const,
  },
  {
    id: "5",
    action: "Fill password field",
    status: "pending" as const,
  },
];

export default function ExecutionStatusExample() {
  return (
    <div className="p-6 max-w-md">
      <ExecutionStatus steps={mockSteps} currentStep={2} />
    </div>
  );
}
