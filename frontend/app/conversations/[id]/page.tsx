"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { ArrowLeft, Send, Check, X, Bot, User } from "lucide-react"
import Link from "next/link"

// TODO: Replace with actual data from API based on lead ID
const leadData = {
  id: 1,
  name: "Krishna",
  car: "",
  status: "new",
  phone: "+19146022064",
  email: "",
}

// TODO: Replace with actual conversation data from API
const messages = [
  {
    id: 1,
    sender: "agent",
    content: "Hi Krishna, this is your dealership agent!",
    timestamp: "Just now",
    type: "message",
    // no 'approved' property for normal messages
  },
]

const statusColors = {
  new: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  warm: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  hot: "bg-red-500/20 text-red-400 border-red-500/30",
  "follow-up": "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  cold: "bg-gray-500/20 text-gray-400 border-gray-500/30",
}

export default function ConversationDetail({ params }: { params: { id: string } }) {
  const [customMessage, setCustomMessage] = useState("")
  const [messageList, setMessageList] = useState(messages)
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)
  const [sendSuccess, setSendSuccess] = useState(false)

  // TODO: Implement API call to approve AI suggestion
  const handleApprove = (messageId: number) => {
    setMessageList((prev) =>
      prev.map((msg) => (msg.id === messageId ? { ...msg, approved: true, sender: "agent", type: "message" } : msg)),
    )
    // TODO: API call to send approved message
    console.log("Approved message:", messageId)
  }

  // TODO: Implement API call to reject AI suggestion
  const handleReject = (messageId: number) => {
    setMessageList((prev) => prev.filter((msg) => msg.id !== messageId))
    // TODO: API call to reject suggestion
    console.log("Rejected message:", messageId)
  }

  // TODO: Implement API call to send custom message
  const handleSendMessage = async () => {
    if (!customMessage.trim()) return
    setSending(true)
    setSendError(null)
    setSendSuccess(false)
    
    const messageToSend = customMessage.trim()
    
    try {
      const res = await fetch("/api/send-message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to: leadData.phone, body: messageToSend }),
      })
      
      if (!res.ok) {
        const data = await res.json()
        setSendError(data.error || "Failed to send message")
      } else {
        setSendSuccess(true)
        // Only add to UI and clear input after successful API call
        const newMessage = {
          id: Date.now(),
          sender: "agent" as const,
          content: messageToSend,
          timestamp: "Just now",
          type: "message" as const,
        }
        setMessageList((prev) => [...prev, newMessage])
        setCustomMessage("")
      }
    } catch (err) {
      setSendError("Failed to send message")
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/conversations">
          <Button variant="ghost" size="icon" className="text-gray-400 hover:text-gray-100">
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-2xl font-bold text-gray-100">{leadData.name}</h2>
            <Badge className={`${statusColors[leadData.status as keyof typeof statusColors]} border`}>
              {leadData.status.charAt(0).toUpperCase() + leadData.status.slice(1)}
            </Badge>
          </div>
          <div className="flex items-center gap-4 text-gray-400 text-sm">
            <span>{leadData.car}</span>
            <span>•</span>
            <span>{leadData.phone}</span>
            <span>•</span>
            <span>{leadData.email}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card className="bg-gray-900/50 border-gray-800 h-[600px] flex flex-col">
            <CardHeader className="border-b border-gray-800">
              <h3 className="font-semibold text-gray-100">Conversation</h3>
            </CardHeader>
            <CardContent className="flex-1 p-0">
              <div className="h-full flex flex-col">
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                  {messageList.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.sender === "lead" ? "justify-start" : "justify-end"}`}
                    >
                      <div
                        className={`max-w-[70%] ${
                          message.sender === "lead"
                            ? "bg-gray-800 text-gray-100"
                            : message.type === "suggestion"
                              ? "bg-blue-900/30 border border-blue-500/30 text-blue-100"
                              : "bg-blue-600 text-white"
                        } rounded-lg p-4`}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          {message.sender === "lead" ? (
                            <User className="w-4 h-4" />
                          ) : message.type === "suggestion" ? (
                            <Bot className="w-4 h-4" />
                          ) : (
                            <User className="w-4 h-4" />
                          )}
                          <span className="text-sm font-medium">
                            {message.sender === "lead"
                              ? leadData.name
                              : message.type === "suggestion"
                                ? "AI Suggestion"
                                : "You"}
                          </span>
                          <span className="text-xs opacity-70">{message.timestamp}</span>
                        </div>
                        <p className="text-sm">{message.content}</p>

                        {message.type === "suggestion" && "approved" in message && !message.approved && (
                          <div className="flex gap-2 mt-3">
                            <Button
                              size="sm"
                              onClick={() => handleApprove(message.id)}
                              className="bg-green-600 hover:bg-green-700 text-white"
                            >
                              <Check className="w-4 h-4 mr-1" />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleReject(message.id)}
                              className="border-red-500 text-red-400 hover:bg-red-500/10"
                            >
                              <X className="w-4 h-4 mr-1" />
                              Reject
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="border-t border-gray-800 p-4">
                  <div className="flex gap-2">
                    <Textarea
                      placeholder="Type your message..."
                      value={customMessage}
                      onChange={(e) => setCustomMessage(e.target.value)}
                      className="flex-1 bg-gray-800 border-gray-700 text-gray-100 placeholder-gray-400 resize-none"
                      rows={2}
                    />
                    <Button onClick={handleSendMessage} className="bg-blue-600 hover:bg-blue-700 text-white self-end">
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                  {sendSuccess && (
                    <p className="text-green-400 text-sm mt-2">Message sent successfully!</p>
                  )}
                  {sendError && (
                    <p className="text-red-400 text-sm mt-2">{sendError}</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div>
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <h3 className="font-semibold text-gray-100">Lead Information</h3>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm text-gray-400">Status</label>
                <Badge className={`${statusColors[leadData.status as keyof typeof statusColors]} border mt-1`}>
                  {leadData.status.charAt(0).toUpperCase() + leadData.status.slice(1)}
                </Badge>
              </div>
              <div>
                <label className="text-sm text-gray-400">Vehicle Interest</label>
                <p className="text-gray-100 font-medium">{leadData.car}</p>
              </div>
              <div>
                <label className="text-sm text-gray-400">Phone</label>
                <p className="text-gray-100">{leadData.phone}</p>
              </div>
              <div>
                <label className="text-sm text-gray-400">Email</label>
                <p className="text-gray-100">{leadData.email}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
