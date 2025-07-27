"use client"
import { Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { WelcomeSection } from "@/components/welcome-section"
import { PerformanceOverview } from "@/components/performance-overview"
import { LeadsSection } from "@/components/leads-section"
import { AlertsSection } from "@/components/alerts-section"

function DashboardContent() {
  const searchParams = useSearchParams()
  const searchTerm = searchParams.get("search") || ""

  return (
    <div className="space-y-8">
      <WelcomeSection />
      <PerformanceOverview />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <LeadsSection searchTerm={searchTerm} />
        </div>
        <div>
          <AlertsSection searchTerm={searchTerm} />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <DashboardContent />
    </Suspense>
  )
}
