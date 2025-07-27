"use client"

import { useMemo } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Globe, Facebook, Instagram, Phone } from "lucide-react"
import Link from "next/link"

// TODO: Replace with actual data from API
const allLeads = [
  {
    id: 1,
    name: "Sarah Johnson",
    car: "2019 Honda Civic",
    source: "Website",
    status: "warm",
    lastContact: "2 hours ago",
  },
  {
    id: 2,
    name: "Mike Chen",
    car: "2021 Toyota Camry",
    source: "Facebook",
    status: "hot",
    lastContact: "30 minutes ago",
  },
  {
    id: 3,
    name: "Emily Davis",
    car: "2020 BMW X3",
    source: "Instagram",
    status: "new",
    lastContact: "Just now",
  },
  {
    id: 4,
    name: "Robert Wilson",
    car: "2018 Ford F-150",
    source: "Phone",
    status: "follow-up",
    lastContact: "3 days ago",
  },
  {
    id: 5,
    name: "Lisa Anderson",
    car: "2022 Tesla Model 3",
    source: "Website",
    status: "cold",
    lastContact: "1 week ago",
  },
]

const sourceIcons = {
  Website: Globe,
  Facebook: Facebook,
  Instagram: Instagram,
  Phone: Phone,
}

const statusColors = {
  new: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  warm: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  hot: "bg-red-500/20 text-red-400 border-red-500/30",
  "follow-up": "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  cold: "bg-gray-500/20 text-gray-400 border-gray-500/30",
}

interface LeadsSectionProps {
  searchTerm?: string
}

export function LeadsSection({ searchTerm = "" }: LeadsSectionProps) {
  // Use useMemo to filter leads based on search term
  const filteredLeads = useMemo(() => {
    if (searchTerm) {
      return allLeads.filter(
        (lead) =>
          lead.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          lead.car.toLowerCase().includes(searchTerm.toLowerCase()) ||
          lead.source.toLowerCase().includes(searchTerm.toLowerCase()) ||
          lead.status.toLowerCase().includes(searchTerm.toLowerCase()),
      )
    }
    return allLeads
  }, [searchTerm])

  return (
    <div>
      <h3 className="text-xl font-semibold text-gray-100 mb-6">Recent Leads</h3>
      <div className="space-y-4">
        {filteredLeads.map((lead, index) => {
          const SourceIcon = sourceIcons[lead.source as keyof typeof sourceIcons]
          return (
            <Link key={lead.id} href={`/conversations/${lead.id}`}>
              <Card
                className="bg-gray-900/50 border-gray-800 hover:bg-gray-900/70 transition-all duration-300 hover:scale-[1.02] cursor-pointer"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-gray-800 rounded-full flex items-center justify-center">
                        <span className="text-gray-300 font-medium">
                          {lead.name
                            .split(" ")
                            .map((n) => n[0])
                            .join("")}
                        </span>
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-100">{lead.name}</h4>
                        <p className="text-gray-400 text-sm">{lead.car}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <SourceIcon className="w-4 h-4 text-gray-500" />
                          <span className="text-gray-500 text-sm">{lead.source}</span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className={`${statusColors[lead.status as keyof typeof statusColors]} border`}>
                        {lead.status.charAt(0).toUpperCase() + lead.status.slice(1)}
                      </Badge>
                      <p className="text-gray-500 text-sm mt-2">{lead.lastContact}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          )
        })}
      </div>

      {filteredLeads.length === 0 && searchTerm && (
        <div className="text-center py-8">
          <h4 className="text-lg font-semibold text-gray-300 mb-2">No leads found</h4>
          <p className="text-gray-400">Try adjusting your search terms.</p>
        </div>
      )}
    </div>
  )
}
