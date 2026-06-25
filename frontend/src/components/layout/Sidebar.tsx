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
  HeartPulse,
  Sparkles,
  Stethoscope,
  Pill,
  User as UserIcon,
  Clock,
  IndianRupee,
  Award,
  Shield,
  Lock,
  BarChart3,
  Cpu,
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
        { name: 'Dashboard', href: '/dashboard/doctor', icon: LayoutDashboard },
        { name: 'Appointments', href: '/dashboard/doctor/appointments', icon: Calendar },
        { name: 'Consultations', href: '/dashboard/doctor/consultations', icon: Stethoscope },
        { name: 'Prescriptions', href: '/dashboard/doctor/prescriptions', icon: Pill },
        { name: 'Patients', href: '/dashboard/patients', icon: Users },
        { name: 'Availability', href: '/dashboard/availability', icon: Clock },
        { name: 'Earnings', href: '/dashboard/earnings', icon: IndianRupee },
        { name: 'Profile', href: '/dashboard/profile', icon: UserIcon },
      ]
    }

    
    if (role === 'admin') {
      return [
        { name: 'Dashboard', href: '/dashboard/admin', icon: LayoutDashboard },
        { name: 'Administrators', href: '/dashboard/admin/admins', icon: Shield },
        { name: 'Security', href: '/dashboard/admin/security', icon: Lock },
        { name: 'Users', href: '/dashboard/admin/users', icon: Users },
        { name: 'Doctors', href: '/dashboard/admin/doctors', icon: Award },
        { name: 'Analytics', href: '/dashboard/admin/analytics', icon: BarChart3 },
        { name: 'System Logs', href: '/dashboard/admin/logs', icon: Activity },
        { name: 'System Health', href: '/dashboard/admin/system', icon: Cpu },
        { name: 'Settings', href: '/dashboard/settings/profile', icon: Settings },
      ]
    }



    // Default: patient — matches v0 screenshot sidebar
    return [
      { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
      { name: 'Nura AI', href: '/dashboard/chat', icon: Sparkles },
      { name: 'Medical History', href: '/dashboard/history', icon: Clock },
      { name: 'Reports', href: '/dashboard/records', icon: FileText },
      { name: 'Doctors', href: '/dashboard/doctors', icon: Stethoscope },
      { name: 'Appointments', href: '/dashboard/appointments', icon: Calendar },
      { name: 'Medications & Reminders', href: '/dashboard/reminders', icon: Pill },
      { name: 'Apply as Doctor', href: '/dashboard/doctor-application', icon: Award },
      { name: 'Profile', href: '/dashboard/settings/profile', icon: UserIcon },
    ]
  }

  const navItems = getNavItems()
  const role = user?.role || 'patient'

  return (
    <div className="flex h-full w-64 flex-col bg-slate-900 text-slate-300 border-r border-slate-800">
      <div className="flex h-16 items-center px-6 border-b border-slate-800">
        <Link href="/dashboard" className="flex items-center gap-2 text-white font-bold text-xl">
          <HeartPulse className="h-6 w-6 text-teal-400" />
          <span>Nura</span>
          {role === 'patient' && (
            <span className="text-xs font-normal text-slate-400 ml-0.5 mt-1">Health Assistant</span>
          )}
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
                    ? "bg-teal-600/20 text-white" 
                    : "hover:bg-slate-800 hover:text-white"
                )}
              >
                <item.icon 
                  className={cn(
                    "mr-3 flex-shrink-0 h-5 w-5",
                    isActive ? "text-teal-400" : "text-slate-400 group-hover:text-teal-400"
                  )} 
                />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Nura AI Help Card — patient only */}
      {role === 'patient' && (
        <div className="p-3">
          <Link href="/dashboard/chat">
            <div className="rounded-lg bg-teal-600/10 border border-teal-600/20 p-4 hover:bg-teal-600/20 transition-colors cursor-pointer">
              <div className="flex items-center gap-2 mb-1">
                <Sparkles className="h-4 w-4 text-teal-400" />
                <span className="text-sm font-semibold text-white">Nura AI</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Ask questions about your health records anytime.
              </p>
            </div>
          </Link>
        </div>
      )}
    </div>
  )
}

