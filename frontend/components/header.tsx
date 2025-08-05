"use client"

import { useState, useEffect } from "react"
import { Search, Bell, User, LogOut } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/components/auth/auth-provider"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const pageNames: Record<string, string> = {
  "/": "Dashboard",
  "/conversations": "Conversations",
  "/templates": "Template Manager",
  "/settings": "Settings",
}

export function Header() {
  const pathname = usePathname()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [searchTerm, setSearchTerm] = useState("")
  const pageName = pageNames[pathname] || "Dashboard"
  const { user, signOut, loading } = useAuth()

  // Initialize search term from URL params
  useEffect(() => {
    const search = searchParams.get("search")
    if (search) {
      setSearchTerm(search)
    }
  }, [searchParams])

  const handleSearch = (value: string) => {
    setSearchTerm(value)

    // Update URL with search parameter
    const params = new URLSearchParams(searchParams.toString())
    if (value) {
      params.set("search", value)
    } else {
      params.delete("search")
    }

    // Update the URL without causing a page reload
    const newUrl = `${pathname}?${params.toString()}`
    router.replace(newUrl, { scroll: false })
  }

  const getSearchPlaceholder = () => {
    switch (pathname) {
      case "/conversations":
        return "Search conversations..."
      case "/":
        return "Search leads, conversations..."
      default:
        return "Search..."
    }
  }

  // Show search bar only on Dashboard and Conversations pages (removed /templates)
  const showSearchBar = pathname === "/" || pathname === "/conversations"

  return (
    <header className="border-b border-gray-800 bg-gray-950/50 backdrop-blur-sm min-w-0">
      <div className="flex items-center justify-between px-6 py-4 min-w-0">
        <div>
          <h1 className="text-2xl font-semibold text-gray-100">{pageName}</h1>
        </div>

        <div className="flex items-center gap-4">
          {showSearchBar && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder={getSearchPlaceholder()}
                value={searchTerm}
                onChange={(e) => handleSearch(e.target.value)}
                className="pl-10 w-80 bg-gray-900/50 border-gray-700 text-gray-100 placeholder-gray-400 focus:border-blue-500 transition-colors"
              />
            </div>
          )}

          <Button
            variant="ghost"
            size="icon"
            className="text-gray-400 hover:text-gray-100 hover:bg-gray-800/50 animate-float transition-all duration-300"
          >
            <Bell className="w-5 h-5" />
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="text-gray-400 hover:text-gray-100 hover:bg-gray-800/50 animate-float transition-all duration-300"
              >
                <User className="w-5 h-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56 mr-2 bg-gray-900 border-gray-800 text-gray-100">
              <DropdownMenuLabel>
                {loading ? 'Loading...' : user?.email || 'My Account'}
              </DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-gray-800" />
              <Link href="/settings">
                <DropdownMenuItem className="cursor-pointer hover:bg-gray-800">
                  Settings
                </DropdownMenuItem>
              </Link>
              <DropdownMenuItem 
                className="cursor-pointer hover:bg-gray-800 text-red-400"
                onClick={() => signOut()}
              >
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
