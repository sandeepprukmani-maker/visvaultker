import { PageCard } from "../page-card"

export default function PageCardExample() {
  return (
    <div className="p-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3 max-w-6xl">
      <PageCard
        title="Login Page"
        url="/login"
        elementCount={12}
      />
      <PageCard
        title="User Dashboard"
        url="/dashboard"
        elementCount={48}
        templateGroup={5}
      />
    </div>
  )
}
