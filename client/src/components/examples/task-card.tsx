import { TaskCard } from "../task-card";

export default function TaskCardExample() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 p-4">
      <TaskCard
        id="task-1"
        title="Send LinkedIn Connection"
        description="Connect with professionals based on criteria"
        website="linkedin.com"
        lastRun="2 hours ago"
        runCount={15}
        status="active"
        onRun={() => console.log("Run task")}
        onEdit={() => console.log("Edit task")}
        onDelete={() => console.log("Delete task")}
      />
      <TaskCard
        id="task-2"
        title="Scrape Product Prices"
        description="Extract pricing data from e-commerce sites"
        website="amazon.com"
        lastRun="1 day ago"
        runCount={42}
        status="active"
        onRun={() => console.log("Run task")}
        onEdit={() => console.log("Edit task")}
        onDelete={() => console.log("Delete task")}
      />
    </div>
  );
}
