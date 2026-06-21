'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuthStore } from '@/stores/auth'
import { 
  LayoutDashboard, 
  Calendar, 
  Users, 
  Settings, 
  FileText,
  Activity,
  HeartPulse
} from 'lucide-react'
import { cn } from '@/lib/utils'

export function Sidebar() {
  const pathname = usePathname()
  const { user } = useAuthStore()

  // Define navigation based on role
  const getNavItems = () => {
    const role = user?.role || 'patient'
    
    if (role === 'doctor') {
      return [
        { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Appointments', href: '/dashboard/appointments', icon: Calendar },
        { name: 'Patients', href: '/dashboard/patients', icon: Users },
        { name: 'Reports', href: '/dashboard/reports', icon: FileText },
        { name: 'Settings', href: '/dashboard/settings/profile', icon: Settings },
      ]
    }
    
    if (role === 'admin') {
      return [
        { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Users', href: '/dashboard/users', icon: Users },
        { name: 'System Logs', href: '/dashboard/logs', icon: Activity },
        { name: 'Settings', href: '/dashboard/settings/profile', icon: Settings },
      ]
    }

    // Default: patient
    return [
      { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
      { name: 'My Appointments', href: '/dashboard/appointments', icon: Calendar },
      { name: 'My Doctors', href: '/dashboard/doctors', icon: HeartPulse },
      { name: 'Medical Records', href: '/dashboard/records', icon: FileText },
      { name: 'Settings', href: '/dashboard/settings/profile', icon: Settings },
    ]
  }

  const navItems = getNavItems()

  return (
    <div className="flex h-full w-64 flex-col bg-slate-900 text-slate-300 border-r border-slate-800">
      <div className="flex h-16 items-center px-6 border-b border-slate-800">
        <Link href="/dashboard" className="flex items-center gap-2 text-white font-bold text-xl">
          <HeartPulse className="h-6 w-6 text-primary" />
          <span>Nura</span>
        </Link>
      </div>
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="space-y-1 px-3">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                  isActive 
                    ? "bg-slate-800 text-white" 
                    : "hover:bg-slate-800 hover:text-white"
                )}
              >
                <item.icon 
                  className={cn(
                    "mr-3 flex-shrink-0 h-5 w-5",
                    isActive ? "text-primary" : "text-slate-400 group-hover:text-primary"
                  )} 
                />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
