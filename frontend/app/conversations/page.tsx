"use client"

import { useMemo } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useSearchParams } from "next/navigation"
import Link from "next/link"

// TODO: Replace with actual data from API
const conversations = [
  {
    id: 1,
    name: "Sarah Johnson",
    car: "2019 Honda Civic",
    status: "warm",
    lastMessage: "I'm interested in scheduling a test drive",
    lastMessageTime: "2 hours ago",
    unreadCount: 2,
  },
  {
    id: 2,
    name: "Mike Chen",
    car: "2021 Toyota Camry",
    status: "hot",
    lastMessage: "What's your best price for this vehicle?",
    lastMessageTime: "30 minutes ago",
    unreadCount: 1,
  },
  {
    id: 3,
    name: "Emily Davis",
    car: "2020 BMW X3",
    status: "new",
    lastMessage: "Hi, I saw your listing online",
    lastMessageTime: "Just now",
    unreadCount: 1,
  },
  {
    id: 4,
    name: "Robert Wilson",
    car: "2018 Ford F-150",
    status: "follow-up",
    lastMessage: "Thanks for the information",
    lastMessageTime: "3 days ago",
    unreadCount: 0,
  },
  {
    id: 5,
    name: "Lisa Anderson",
    car: "2022 Tesla Model 3",
    status: "cold",
    lastMessage: "I'll think about it",
    lastMessageTime: "1 week ago",
    unreadCount: 0,
  },
]

const statusColors = {
  new: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  warm: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  hot: "bg-red-500/20 text-red-400 border-red-500/30",
  "follow-up": "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  cold: "bg-gray-500/20 text-gray-400 border-gray-500/30",
}

const statusDescriptions = {
  new: "Just contacted Lead within 1 day",
  warm: "Lead has just responded to the email",
  hot: "Lead is in a 3+ email thread with the agent",
  "follow-up": "Lead has not responded for 1-4 days",
  cold: "Lead has not responded for 4+ days",
}

export default function Conversations() {
  const searchParams = useSearchParams()
  const searchTerm = searchParams.get("search") || ""

  // Use useMemo to filter conversations based on search term
  const filteredConversations = useMemo(() => {
    if (searchTerm) {
      return conversations.filter(
        (conversation) =>
          conversation.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          conversation.car.toLowerCase().includes(searchTerm.toLowerCase()) ||
          conversation.lastMessage.toLowerCase().includes(searchTerm.toLowerCase()) ||
          conversation.status.toLowerCase().includes(searchTerm.toLowerCase()),
      )
    }
    return conversations
  }, [searchTerm])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-100">Conversations</h2>
          <p className="text-gray-400">Manage your lead conversations</p>
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
                      </div>
                      <p className="text-gray-400 text-sm mb-1">{conversation.car}</p>
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
    </div>
  )
}
