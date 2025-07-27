import type React from "react"
import type { Metadata } from "next"
import { Inter } from 'next/font/google'
import "./globals.css"
import { SidebarProvider } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { Header } from "@/components/header"
import { AuthProvider } from "@/components/auth/auth-provider"
import { ThemeProvider } from "@/components/theme-provider"
import { Toaster } from "@/components/ui/sonner"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Maqro - Lead Management Dashboard",
  description: "Premium CRM for lead management and conversations"
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-gray-950 text-gray-100`}>
        <ThemeProvider attribute="class" defaultTheme="dark">
          <AuthProvider>
            <SidebarProvider defaultOpen={true}>
              <div className="flex min-h-screen w-full bg-gray-950">
                <AppSidebar />
                <div className="flex-1 flex flex-col min-w-0">
                  <Header />
                  <main className="flex-1 p-4 md:p-6 overflow-auto">{children}</main>
                </div>
              </div>
            </SidebarProvider>
          </AuthProvider>
        </ThemeProvider>
        <Toaster />
      </body>
    </html>
  )
}
