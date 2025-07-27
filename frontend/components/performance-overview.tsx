import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Users, Flame, Clock, Calendar, DollarSign } from "lucide-react"

const stats = [
  {
    title: "Total Leads",
    value: "1,247",
    change: "+12%",
    icon: Users,
    color: "text-blue-400",
  },
  {
    title: "Warm Leads",
    value: "342",
    change: "+8%",
    icon: Flame,
    color: "text-orange-400",
  },
  {
    title: "Avg Response Time",
    value: "2.4h",
    change: "-15%",
    icon: Clock,
    color: "text-green-400",
  },
  {
    title: "Booked Appointments",
    value: "89",
    change: "+23%",
    icon: Calendar,
    color: "text-purple-400",
  },
  {
    title: "Deals Closed",
    value: "$47,500",
    change: "+31%",
    icon: DollarSign,
    color: "text-emerald-400",
  },
]

export function PerformanceOverview() {
  return (
    <div>
      <h3 className="text-xl font-semibold text-gray-100 mb-6">Performance Overview</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        {stats.map((stat, index) => (
          <Card
            key={stat.title}
            className="bg-gray-900/50 border-gray-800 hover:bg-gray-900/70 transition-all duration-300 hover:scale-105"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-400">{stat.title}</CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-100">{stat.value}</div>
              <p className={`text-xs ${stat.change.startsWith("+") ? "text-green-400" : "text-red-400"}`}>
                {stat.change} from last month
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
