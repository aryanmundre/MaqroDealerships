"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Search, Plus, Edit, Trash2, Copy, MessageSquare, Mail, Phone } from "lucide-react"

// TODO: Replace with actual data from API
const templates = [
  {
    id: 1,
    name: "Initial Contact - Website Lead",
    category: "First Contact",
    type: "email",
    subject: "Thanks for your interest in our vehicles!",
    content:
      "Hi {{name}},\n\nThank you for your interest in the {{vehicle}}. I'd love to help you find the perfect car that meets your needs.\n\nWould you be available for a quick call this week to discuss your requirements?\n\nBest regards,\n{{agent_name}}",
    usage: 45,
    lastUsed: "2 days ago",
  },
  {
    id: 2,
    name: "Follow-up - No Response",
    category: "Follow-up",
    type: "email",
    subject: "Still interested in the {{vehicle}}?",
    content:
      "Hi {{name}},\n\nI wanted to follow up on your interest in the {{vehicle}}. I know you're probably busy, but I wanted to make sure you didn't miss out on this great opportunity.\n\nThe vehicle is still available and I'd be happy to answer any questions you might have.\n\nLet me know if you'd like to schedule a test drive!\n\nBest,\n{{agent_name}}",
    usage: 32,
    lastUsed: "1 day ago",
  },
  {
    id: 3,
    name: "Appointment Confirmation",
    category: "Scheduling",
    type: "sms",
    subject: "",
    content:
      "Hi {{name}}, this is {{agent_name}} from {{dealership}}. Just confirming your appointment tomorrow at {{time}} to see the {{vehicle}}. See you then!",
    usage: 28,
    lastUsed: "3 hours ago",
  },
  {
    id: 4,
    name: "Price Quote Follow-up",
    category: "Pricing",
    type: "email",
    subject: "Your personalized quote for {{vehicle}}",
    content:
      "Hi {{name}},\n\nAs promised, here's your personalized quote for the {{vehicle}}:\n\nVehicle Price: ${{price}}\nTrade-in Value: ${{trade_value}}\nYour Price: ${{final_price}}\n\nThis quote is valid for the next 7 days. Would you like to move forward with financing options?\n\nBest regards,\n{{agent_name}}",
    usage: 19,
    lastUsed: "5 days ago",
  },
]

const categories = ["All", "First Contact", "Follow-up", "Scheduling", "Pricing", "Closing"]
const types = ["email", "sms", "call"]

export default function Templates() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("All")
  const [selectedType, setSelectedType] = useState("all")
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [newTemplate, setNewTemplate] = useState({
    name: "",
    category: "",
    type: "email",
    subject: "",
    content: "",
  })

  const filteredTemplates = templates.filter((template) => {
    const matchesSearch =
      template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.content.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === "All" || template.category === selectedCategory
    const matchesType = selectedType === "all" || template.type === selectedType

    return matchesSearch && matchesCategory && matchesType
  })

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "email":
        return <Mail className="w-4 h-4" />
      case "sms":
        return <MessageSquare className="w-4 h-4" />
      case "call":
        return <Phone className="w-4 h-4" />
      default:
        return <MessageSquare className="w-4 h-4" />
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case "email":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30"
      case "sms":
        return "bg-green-500/20 text-green-400 border-green-500/30"
      case "call":
        return "bg-purple-500/20 text-purple-400 border-purple-500/30"
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30"
    }
  }

  const handleCreateTemplate = () => {
    // TODO: API call to create template
    console.log("Creating template:", newTemplate)
    setIsCreateDialogOpen(false)
    setNewTemplate({ name: "", category: "", type: "email", subject: "", content: "" })
  }

  return (
    <div className="w-full max-w-none space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-gray-100">Template Manager</h2>
          <p className="text-gray-400 mt-2">Create and manage your message templates</p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-blue-600 hover:bg-blue-700 text-white">
              <Plus className="w-4 h-4 mr-2" />
              Create Template
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-gray-900 border-gray-800 text-gray-100 max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New Template</DialogTitle>
            </DialogHeader>
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="template-name" className="text-gray-300">
                    Template Name
                  </Label>
                  <Input
                    id="template-name"
                    value={newTemplate.name}
                    onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
                    className="bg-gray-800 border-gray-700 text-gray-100"
                    placeholder="e.g., Initial Contact - Facebook Lead"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="template-category" className="text-gray-300">
                    Category
                  </Label>
                  <Select
                    value={newTemplate.category}
                    onValueChange={(value) => setNewTemplate({ ...newTemplate, category: value })}
                  >
                    <SelectTrigger className="bg-gray-800 border-gray-700 text-gray-100">
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-gray-700">
                      {categories.slice(1).map((category) => (
                        <SelectItem key={category} value={category}>
                          {category}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="template-type" className="text-gray-300">
                    Type
                  </Label>
                  <Select
                    value={newTemplate.type}
                    onValueChange={(value) => setNewTemplate({ ...newTemplate, type: value })}
                  >
                    <SelectTrigger className="bg-gray-800 border-gray-700 text-gray-100">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-gray-700">
                      <SelectItem value="email">Email</SelectItem>
                      <SelectItem value="sms">SMS</SelectItem>
                      <SelectItem value="call">Call Script</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {newTemplate.type === "email" && (
                  <div className="space-y-2">
                    <Label htmlFor="template-subject" className="text-gray-300">
                      Subject Line
                    </Label>
                    <Input
                      id="template-subject"
                      value={newTemplate.subject}
                      onChange={(e) => setNewTemplate({ ...newTemplate, subject: e.target.value })}
                      className="bg-gray-800 border-gray-700 text-gray-100"
                      placeholder="e.g., Thanks for your interest!"
                    />
                  </div>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="template-content" className="text-gray-300">
                  Template Content
                </Label>
                <Textarea
                  id="template-content"
                  value={newTemplate.content}
                  onChange={(e) => setNewTemplate({ ...newTemplate, content: e.target.value })}
                  className="bg-gray-800 border-gray-700 text-gray-100 min-h-[200px]"
                  placeholder="Use {{name}}, {{vehicle}}, {{agent_name}} for dynamic content..."
                />
                <p className="text-xs text-gray-400">
                  Use variables like {`{name}`}, {`{vehicle}`}, {`{agent_name}`} for personalization
                </p>
              </div>
              <div className="flex justify-end gap-3">
                <Button
                  variant="outline"
                  onClick={() => setIsCreateDialogOpen(false)}
                  className="border-gray-600 text-gray-300"
                >
                  Cancel
                </Button>
                <Button onClick={handleCreateTemplate} className="bg-blue-600 hover:bg-blue-700 text-white">
                  Create Template
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-gray-900/50 border-gray-700 text-gray-100 placeholder-gray-400 focus:border-blue-500"
          />
        </div>
        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-full sm:w-48 bg-gray-900/50 border-gray-700 text-gray-100">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-gray-800 border-gray-700">
            {categories.map((category) => (
              <SelectItem key={category} value={category}>
                {category}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={selectedType} onValueChange={setSelectedType}>
          <SelectTrigger className="w-full sm:w-32 bg-gray-900/50 border-gray-700 text-gray-100">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-gray-800 border-gray-700">
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="email">Email</SelectItem>
            <SelectItem value="sms">SMS</SelectItem>
            <SelectItem value="call">Call</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredTemplates.map((template, index) => (
          <Card
            key={template.id}
            className="bg-gray-900/50 border-gray-800 hover:bg-gray-900/70 transition-all duration-300 hover:scale-[1.02]"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg font-semibold text-gray-100 mb-2">{template.name}</CardTitle>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className="bg-gray-700/50 text-gray-300 border-gray-600">{template.category}</Badge>
                    <Badge className={`${getTypeColor(template.type)} border flex items-center gap-1`}>
                      {getTypeIcon(template.type)}
                      {template.type.toUpperCase()}
                    </Badge>
                  </div>
                </div>
              </div>
              {template.subject && (
                <div className="text-sm text-gray-400">
                  <strong>Subject:</strong> {template.subject}
                </div>
              )}
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-4">
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <p className="text-sm text-gray-300 line-clamp-4">{template.content}</p>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Used {template.usage} times</span>
                  <span>Last used {template.lastUsed}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 border-gray-600 text-gray-300 hover:bg-gray-800 bg-transparent"
                  >
                    <Edit className="w-3 h-3 mr-1" />
                    Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-gray-600 text-gray-300 hover:bg-gray-800 bg-transparent"
                  >
                    <Copy className="w-3 h-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-red-600 text-red-400 hover:bg-red-500/10 bg-transparent"
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <MessageSquare className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-300 mb-2">No templates found</h3>
          <p className="text-gray-400 mb-4">Try adjusting your search or filters, or create a new template.</p>
          <Button onClick={() => setIsCreateDialogOpen(true)} className="bg-blue-600 hover:bg-blue-700 text-white">
            <Plus className="w-4 h-4 mr-2" />
            Create Your First Template
          </Button>
        </div>
      )}
    </div>
  )
}
