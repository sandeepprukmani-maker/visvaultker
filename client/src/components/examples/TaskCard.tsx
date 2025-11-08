import { TaskCard } from '../TaskCard';

export default function TaskCardExample() {
  return (
    <div className="p-6 max-w-md space-y-4">
      <TaskCard
        id="1"
        name="Amazon Product Search"
        description="Searches for products on Amazon and extracts pricing information with screenshots"
        language="TypeScript"
        status="success"
        lastRun="2 hours ago"
        onRun={() => console.log('Run task')}
        onEdit={() => console.log('Edit task')}
        onDelete={() => console.log('Delete task')}
        onDuplicate={() => console.log('Duplicate task')}
      />
      <TaskCard
        id="2"
        name="LinkedIn Profile Scraper"
        description="Extracts public profile information and connection data"
        language="JavaScript"
        status="failed"
        lastRun="1 day ago"
        onRun={() => console.log('Run task')}
        onEdit={() => console.log('Edit task')}
        onDelete={() => console.log('Delete task')}
        onDuplicate={() => console.log('Duplicate task')}
      />
    </div>
  );
}
