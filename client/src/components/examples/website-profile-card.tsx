import { WebsiteProfileCard } from "../website-profile-card";

export default function WebsiteProfileCardExample() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 p-4">
      <WebsiteProfileCard
        id="linkedin"
        url="linkedin.com"
        elementCount={247}
        lastLearned="2 days ago"
        version={3}
        status="learned"
        onView={() => console.log("View profile")}
        onRelearn={() => console.log("Relearn website")}
      />
      <WebsiteProfileCard
        id="twitter"
        url="twitter.com"
        elementCount={189}
        lastLearned="1 week ago"
        version={2}
        status="outdated"
        onView={() => console.log("View profile")}
        onRelearn={() => console.log("Relearn website")}
      />
    </div>
  );
}
