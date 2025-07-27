"use client"

import { useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle, Clock } from "lucide-react"

// TODO: Replace with actual data from API
const allAlerts = [
  {
    id: 1,
    type: "action-needed",
    title: "Action Needed",
    message: "Sarah Johnson requires immediate follow-up",
    leadName: "Sarah Johnson",
    time: "2 hours ago",
  },
  {
    id: 2,
    type: "follow-up",
    title: "Follow-Up",
    message: "Mike Chen hasn't responded in 3 days",
    leadName: "Mike Chen",
    time: "3 days ago",
  },
  {
    id: 3,
    type: "action-needed",
    title: "Action Needed",
    message: "Emily Davis is ready to schedule appointment",
    leadName: "Emily Davis",
    time: "1 hour ago",
  },
]

interface AlertsSectionProps {
  searchTerm?: string
}

export function AlertsSection({ searchTerm = "" }: AlertsSectionProps) {
  // Use useMemo to filter alerts based on search term
  const filteredAlerts = useMemo(() => {
    if (searchTerm) {
      return allAlerts.filter(
        (alert) =>
          alert.leadName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          alert.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
          alert.title.toLowerCase().includes(searchTerm.toLowerCase()),
      )
    }
    return allAlerts
  }, [searchTerm])

  return (
    <div>
      <h3 className="text-xl font-semibold text-gray-100 mb-6">Alerts</h3>
      <div className="space-y-4">
        {filteredAlerts.map((alert, index) => (
          <Card
            key={alert.id}
            className="bg-gray-900/50 border-gray-800 hover:bg-gray-900/70 transition-all duration-300"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  {alert.type === "action-needed" ? (
                    <AlertTriangle className="w-4 h-4 text-red-400" />
                  ) : (
                    <Clock className="w-4 h-4 text-yellow-400" />
                  )}
                  <Badge
                    className={
                      alert.type === "action-needed"
                        ? "bg-red-500/20 text-red-400 border-red-500/30"
                        : "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                    }
                  >
                    {alert.title}
                  </Badge>
                </CardTitle>
                <span className="text-xs text-gray-500">{alert.time}</span>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-gray-300 text-sm mb-2">{alert.message}</p>
              <p className="text-gray-500 text-xs">Lead: {alert.leadName}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredAlerts.length === 0 && searchTerm && (
        <div className="text-center py-8">
          <h4 className="text-lg font-semibold text-gray-300 mb-2">No alerts found</h4>
          <p className="text-gray-400">Try adjusting your search terms.</p>
        </div>
      )}
    </div>
  )
}
