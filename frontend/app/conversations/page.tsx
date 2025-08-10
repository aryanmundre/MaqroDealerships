"use client"

import { useState, useEffect, useMemo } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { getLeadsWithConversations, type LeadWithConversationSummary } from "@/lib/conversations-api"

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

const statusDescriptions = {
  new: "Just contacted Lead within 1 day",
  warm: "Lead has just responded to the email",
  hot: "Lead is in a 3+ email thread with the agent",
  "follow-up": "Lead has not responded for 1-4 days",
  cold: "Lead has not responded for 4+ days",
  "appointment_booked": "Customer has scheduled an appointment",
  "deal_won": "Deal closed successfully",
  "deal_lost": "Deal was lost or customer went elsewhere",
}

export default function Conversations() {
  const searchParams = useSearchParams()
  const searchTerm = searchParams.get("search") || ""
  
  const [conversations, setConversations] = useState<LeadWithConversationSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch conversations on component mount
  useEffect(() => {
    async function fetchConversations() {
      try {
        setLoading(true)
        setError(null)
        console.log('Starting to fetch conversations...')
        const data = await getLeadsWithConversations()
        console.log('Fetched conversations data:', data)
        setConversations(data)
      } catch (err) {
        console.error('Error fetching conversations:', err)
        let errorMessage = 'Failed to fetch conversations'
        
        if (err instanceof Error) {
          if (err.message.includes('User not authenticated')) {
            errorMessage = 'You need to be logged in to view conversations'
          } else if (err.message.includes('Failed to fetch') || err.message.includes('Network')) {
            errorMessage = 'Unable to connect to the server. Please check if the backend is running on http://localhost:8000'
          } else {
            errorMessage = err.message
          }
        }
        
        setError(errorMessage)
      } finally {
        setLoading(false)
      }
    }

    fetchConversations()
  }, [])

  // Use useMemo to filter conversations based on search term
  const filteredConversations = useMemo(() => {
    if (searchTerm) {
      return conversations.filter(
        (conversation) =>
          conversation.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (conversation.car_interest && conversation.car_interest.toLowerCase().includes(searchTerm.toLowerCase())) ||
          conversation.lastMessage.toLowerCase().includes(searchTerm.toLowerCase()) ||
          conversation.status.toLowerCase().includes(searchTerm.toLowerCase()),
      )
    }
    return conversations
  }, [searchTerm, conversations])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-100">Conversations</h2>
            <p className="text-gray-400">Manage your lead conversations</p>
          </div>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="text-gray-400">Loading conversations...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-100">Conversations</h2>
            <p className="text-gray-400">Manage your lead conversations</p>
          </div>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-red-400 mb-2">Error loading conversations</h3>
            <p className="text-gray-400">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-100">Conversations</h2>
          <p className="text-gray-400">Manage your lead conversations ({conversations.length} leads)</p>
        </div>
      </div>

      <div className="grid gap-4">
        {filteredConversations.map((conversation, index) => (
          <Link key={conversation.id} href={`/conversations/${conversation.id}`}>
            <Card
              className="bg-gray-900/50 border-gray-800 hover:bg-gray-900/70 transition-all duration-300 hover:scale-[1.01] cursor-pointer"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <div className="w-12 h-12 bg-gray-800 rounded-full flex items-center justify-center">
                        <span className="text-gray-300 font-medium">
                          {conversation.name
                            .split(" ")
                            .map((n) => n[0])
                            .join("")}
                        </span>
                      </div>
                      {conversation.unreadCount > 0 && (
                        <div className="absolute -top-1 -right-1 w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center">
                          <span className="text-xs text-white font-medium">{conversation.unreadCount}</span>
                        </div>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <h4 className="font-semibold text-gray-100">{conversation.name}</h4>
                        <Badge
                          className={`${statusColors[conversation.status as keyof typeof statusColors]} border text-xs`}
                          title={statusDescriptions[conversation.status as keyof typeof statusDescriptions]}
                        >
                          {conversation.status.charAt(0).toUpperCase() + conversation.status.slice(1)}
                        </Badge>
                        {conversation.conversationCount > 0 && (
                          <span className="text-xs text-gray-500">
                            {conversation.conversationCount} message{conversation.conversationCount !== 1 ? 's' : ''}
                          </span>
                        )}
                      </div>
                      <p className="text-gray-400 text-sm mb-1">{conversation.car_interest}</p>
                      <p className="text-gray-300 text-sm">{conversation.lastMessage}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-gray-500 text-sm">{conversation.lastMessageTime}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {filteredConversations.length === 0 && searchTerm && (
        <div className="text-center py-12">
          <h3 className="text-lg font-semibold text-gray-300 mb-2">No conversations found</h3>
          <p className="text-gray-400">Try adjusting your search terms.</p>
        </div>
      )}
      
      {filteredConversations.length === 0 && !searchTerm && !loading && (
         <div className="text-center py-12">
          <h3 className="text-lg font-semibold text-gray-300 mb-2">No conversations yet</h3>
          <p className="text-gray-400">Start by creating some leads to see conversations here.</p>
        </div>
      )}
    </div>
  )
}
