import { Zap, Target, BarChart3 } from "lucide-react"

const features = [
  {
    icon: Zap,
    title: "Respond instantly with AI",
    description: "Automated responses that feel personal and human"
  },
  {
    icon: Target,
    title: "Prioritize high-value leads",
    description: "AI identifies your best opportunities automatically"
  },
  {
    icon: BarChart3,
    title: "Track team performance in real time",
    description: "Monitor conversions and optimize your sales process"
  }
]

export function FeatureList() {
  return (
    <div className="py-24 px-4 sm:px-6 lg:px-8 bg-gray-900/50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Why Dealerships Choose Maqro
          </h2>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Stop losing leads to slow responses. Start closing deals faster.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="group p-8 rounded-2xl bg-gray-800/50 border border-gray-700 hover:border-gray-600 transition-all duration-300 hover:bg-gray-800/70"
            >
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              
              <h3 className="text-xl font-semibold text-white mb-3">
                {feature.title}
              </h3>
              
              <p className="text-gray-300 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
} 