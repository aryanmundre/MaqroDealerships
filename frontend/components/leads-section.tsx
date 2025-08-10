"use client"

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Globe, Facebook, Instagram, Phone } from "lucide-react"
import Link from "next/link"
import { getMyLeads } from "@/lib/leads-api"
import { Lead } from "@/lib/supabase"
import { useAuth } from "@/components/auth/auth-provider"

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
  "appointment_booked": "bg-purple-500/20 text-purple-400 border-purple-500/30",
  "deal_won": "bg-green-500/20 text-green-400 border-green-500/30",
  "deal_lost": "bg-red-600/20 text-red-300 border-red-600/30",
}

interface LeadsSectionProps {
  searchTerm?: string
}

export function LeadsSection({ searchTerm = "" }: LeadsSectionProps) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  // Fetch leads from Supabase
  useEffect(() => {
    async function fetchLeads() {
      try {
        setLoading(true);
        const data = await getMyLeads(searchTerm);
        setLeads(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching leads:', err);
        setError('Failed to load leads. Please try again.');
        setLeads([]);
      } finally {
        setLoading(false);
      }
    }

    if (user) {
      fetchLeads();
    }
  }, [searchTerm, user]);

  // Filter leads based on search term (additional client-side filtering)
  const filteredLeads = leads;

  return (
    <div>
      <h3 className="text-xl font-semibold text-gray-100 mb-6">Recent Leads</h3>
      
      {loading ? (
        <div className="text-center py-8">
          <p className="text-gray-400">Loading leads...</p>
        </div>
      ) : error ? (
        <div className="text-center py-8">
          <h4 className="text-lg font-semibold text-gray-300 mb-2">Error</h4>
          <p className="text-gray-400">{error}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredLeads.map((lead, index) => {
            const SourceIcon = sourceIcons[lead.source as keyof typeof sourceIcons] || Globe
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
                              .map((n: string) => n[0])
                              .join("")}
                          </span>
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-100">{lead.name}</h4>
                          <p className="text-gray-400 text-sm">{lead.car_interest}</p>
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
                        <p className="text-gray-500 text-sm mt-2">{lead.last_contact_at}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            )
          })}
          
          {filteredLeads.length === 0 && (
            <div className="text-center py-8">
              <h4 className="text-lg font-semibold text-gray-300 mb-2">No leads found</h4>
              <p className="text-gray-400">{searchTerm ? 'Try adjusting your search terms.' : 'Add your first lead to get started.'}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
