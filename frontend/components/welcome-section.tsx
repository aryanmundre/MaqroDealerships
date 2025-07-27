import { Button } from "@/components/ui/button"
import { ArrowRight } from 'lucide-react'
import Link from "next/link"

export function WelcomeSection() {
  return (
    <div className="bg-gradient-to-r from-gray-900/50 to-gray-800/30 rounded-xl p-8 border border-gray-800">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-100 mb-2">Welcome to Maqro</h2>
          <p className="text-gray-400 text-lg">Manage your leads and conversations efficiently</p>
        </div>
        <Link href="/conversations">
          <Button
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-all duration-300 hover:scale-105 animate-float"
          >
            Get Started
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </Link>
      </div>
    </div>
  )
}
