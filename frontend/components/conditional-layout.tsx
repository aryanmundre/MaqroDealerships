"use client"

import { useAuth } from "@/components/auth/auth-provider"
import { LandingNav } from "@/components/landing-nav"
import { AppNav } from "@/components/app-nav"

export function ConditionalLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="text-white">Loading...</div>
      </div>
    )
  }

  // Show app layout for authenticated users, landing layout for unauthenticated users
  return user ? (
    <AppNav>{children}</AppNav>
  ) : (
    <LandingNav>{children}</LandingNav>
  )
} 