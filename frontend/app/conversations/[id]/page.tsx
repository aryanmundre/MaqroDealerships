"use client"

import { useState, useEffect, use, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ArrowLeft, Send, Check, X, Bot, User, MessageSquare, Phone } from "lucide-react"
import Link from "next/link"
import { getMyLeadById } from "@/lib/leads-api"
import { getConversations, addMessage } from "@/lib/conversations-api"
import { sendSMS } from "@/lib/sms-api"
import type { Lead, Conversation } from "@/lib/supabase"

const statusColors = {
  new: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  warm: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  hot: "bg-red-500/20 text-red-400 border-red-500/30",
  "follow-up": "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  cold: "bg-gray-500/20 text-gray-400 border-gray-500/30",
}

export default function ConversationDetail({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const [leadData, setLeadData] = useState<Lead | null>(null)
  const [customMessage, setCustomMessage] = useState("")
  const [smsMessage, setSmsMessage] = useState("")
  const [messageList, setMessageList] = useState<Conversation[]>([])
  const [sending, setSending] = useState(false)
  const [sendingSMS, setSendingSMS] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)
  const [smsError, setSmsError] = useState<string | null>(null)
  const [sendSuccess, setSendSuccess] = useState(false)
  const [smsSuccess, setSmsSuccess] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    async function fetchData() {
      const lead = await getMyLeadById(resolvedParams.id)
      setLeadData(lead)
      const conversations = await getConversations(resolvedParams.id)
      setMessageList(conversations)
    }
    fetchData()
  }, [resolvedParams.id])

  // Scroll to bottom on initial load and new messages  
  useEffect(() => {
    if (messagesContainerRef.current && messageList.length > 0) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
    }
  }, [messageList])

  const handleSendMessage = async () => {
    if (!customMessage.trim() || !leadData) return
    setSending(true)
    setSendError(null)
    setSendSuccess(false)
    
    const messageToSend = customMessage.trim()
    
    try {
      const newMessage = await addMessage(leadData.id, messageToSend)
      setSendSuccess(true)
      setMessageList((prev) => [...prev, newMessage])
      setCustomMessage("")
    } catch (err) {
      setSendError("Failed to send message")
    } finally {
      setSending(false)
    }
  }

  const handleSendSMS = async () => {
    if (!smsMessage.trim() || !leadData?.phone) return
    setSendingSMS(true)
    setSmsError(null)
    setSmsSuccess(false)
    
    const messageToSend = smsMessage.trim()
    
    try {
      // Send SMS via backend
      const smsResult = await sendSMS(leadData.phone, messageToSend)
      
      if (smsResult.success) {
        // Also save as a conversation message
        const newMessage = await addMessage(leadData.id, `SMS: ${messageToSend}`)
        setSmsSuccess(true)
        setMessageList((prev) => [...prev, newMessage])
        setSmsMessage("")
      } else {
        setSmsError(smsResult.error || "Failed to send SMS")
      }
    } catch (err) {
      setSmsError("Failed to send SMS")
    } finally {
      setSendingSMS(false)
    }
  }

  if (!leadData) {
    return <div>Loading...</div>
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
            <span>{leadData.car_interest}</span>
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
            <CardHeader className="border-b border-gray-800 flex-shrink-0">
              <h3 className="font-semibold text-gray-100">Conversation</h3>
            </CardHeader>
            <CardContent className="flex-1 p-0 overflow-hidden">
              <div className="h-full flex flex-col">
                <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-6 space-y-4 min-h-0">
                  {messageList.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.sender === "customer" ? "justify-start" : "justify-end"}`}
                    >
                      <div
                        className={`max-w-[70%] ${
                          message.sender === "customer"
                            ? "bg-gray-800 text-gray-100"
                            : "bg-blue-600 text-white"
                        } rounded-lg p-4`}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          {message.sender === "customer" ? (
                            <User className="w-4 h-4" />
                          ) : (
                            <Bot className="w-4 h-4" />
                          )}
                          <span className="text-sm font-medium">
                            {message.sender === "customer"
                              ? leadData.name
                              : "Agent"}
                          </span>
                          <span className="text-xs opacity-70">{new Date(message.created_at).toLocaleTimeString()}</span>
                        </div>
                        <p className="text-sm">{message.message}</p>
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>

                <div className="border-t border-gray-800 p-4 flex-shrink-0">
                  <Tabs defaultValue="message" className="w-full">
                    <TabsList className="grid w-full grid-cols-2 bg-gray-800 border-gray-700">
                      <TabsTrigger value="message" className="flex items-center gap-2 data-[state=active]:bg-gray-700">
                        <MessageSquare className="w-4 h-4" />
                        Internal Message
                      </TabsTrigger>
                      <TabsTrigger 
                        value="sms" 
                        className="flex items-center gap-2 data-[state=active]:bg-gray-700"
                        disabled={!leadData?.phone}
                      >
                        <Phone className="w-4 h-4" />
                        SMS {!leadData?.phone && "(No phone)"}
                      </TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="message" className="mt-4">
                      <div className="flex gap-2">
                        <Textarea
                          placeholder="Type your internal message..."
                          value={customMessage}
                          onChange={(e) => setCustomMessage(e.target.value)}
                          className="flex-1 bg-gray-800 border-gray-700 text-gray-100 placeholder-gray-400 resize-none"
                          rows={2}
                          disabled={sending}
                        />
                        <Button 
                          onClick={handleSendMessage} 
                          disabled={sending || !customMessage.trim()}
                          className="bg-blue-600 hover:bg-blue-700 text-white self-end"
                        >
                          {sending ? <div className="w-4 h-4 animate-spin rounded-full border-2 border-white border-t-transparent" /> : <Send className="w-4 h-4" />}
                        </Button>
                      </div>
                      {sendSuccess && (
                        <p className="text-green-400 text-sm mt-2">Message sent successfully!</p>
                      )}
                      {sendError && (
                        <p className="text-red-400 text-sm mt-2">{sendError}</p>
                      )}
                    </TabsContent>
                    
                    <TabsContent value="sms" className="mt-4">
                      <div className="flex gap-2">
                        <Textarea
                          placeholder={`Send SMS to ${leadData?.phone || 'phone number not available'}...`}
                          value={smsMessage}
                          onChange={(e) => setSmsMessage(e.target.value)}
                          className="flex-1 bg-gray-800 border-gray-700 text-gray-100 placeholder-gray-400 resize-none"
                          rows={2}
                          disabled={sendingSMS || !leadData?.phone}
                        />
                        <Button 
                          onClick={handleSendSMS} 
                          disabled={sendingSMS || !smsMessage.trim() || !leadData?.phone}
                          className="bg-green-600 hover:bg-green-700 text-white self-end"
                        >
                          {sendingSMS ? <div className="w-4 h-4 animate-spin rounded-full border-2 border-white border-t-transparent" /> : <Phone className="w-4 h-4" />}
                        </Button>
                      </div>
                      {smsSuccess && (
                        <p className="text-green-400 text-sm mt-2">SMS sent successfully!</p>
                      )}
                      {smsError && (
                        <p className="text-red-400 text-sm mt-2">{smsError}</p>
                      )}
                      {leadData?.phone && (
                        <p className="text-gray-400 text-xs mt-2">SMS will be sent to {leadData.phone}</p>
                      )}
                    </TabsContent>
                  </Tabs>
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
                <p className="text-gray-100 font-medium">{leadData.car_interest}</p>
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
