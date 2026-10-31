'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/auth'
import { Bell, Search, LogOut, User as UserIcon } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { toast } from 'sonner'

export function Topbar() {
  const { user, logout } = useAuthStore()
  const router = useRouter()
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

  const handleLogout = () => {
    logout()
    toast.success('Successfully logged out')
    router.push('/auth/login')
  }

  const [isNotifOpen, setIsNotifOpen] = useState(false)

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      <div className="flex-1"></div>
      
      <div className="flex items-center gap-4">
        <div className="relative">
          <button 
            onClick={() => setIsNotifOpen(!isNotifOpen)}
            className="relative p-2 text-slate-400 hover:text-slate-600 transition-colors rounded-full hover:bg-slate-100"
          >
            <Bell className="h-5 w-5" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-teal-500"></span>
          </button>

          {isNotifOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setIsNotifOpen(false)}></div>
              <div className="absolute right-0 mt-2 w-72 rounded-md bg-white p-4 shadow-lg ring-1 ring-black ring-opacity-5 z-20">
                <h4 className="text-xs font-bold text-slate-900 border-b pb-2 mb-2">Notifications</h4>
                <div className="text-xs text-slate-500 py-3 text-center">
                  No new notifications right now.
                </div>
              </div>
            </>
          )}
        </div>
        
        <div className="relative">
          <button 
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 focus:outline-none"
          >
            {user?.profile_picture ? (
              <img 
                src={user.profile_picture} 
                alt={user.full_name || 'User'} 
                className="h-8 w-8 rounded-full object-cover border border-primary/20" 
              />
            ) : (
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold border border-primary/20">
                {user?.full_name?.charAt(0).toUpperCase() || 'U'}
              </div>
            )}
            <div className="hidden md:flex flex-col items-start text-sm">
              <span className="font-medium text-slate-700 leading-none">{user?.full_name}</span>
              <span className="text-xs text-slate-500 mt-1 capitalize">{user?.role || 'Patient'}</span>
            </div>
          </button>

          {isDropdownOpen && (
            <>
              <div 
                className="fixed inset-0 z-10" 
                onClick={() => setIsDropdownOpen(false)}
              ></div>
              <div className="absolute right-0 mt-2 w-48 rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 z-20">
                <div className="px-4 py-2.5 border-b flex items-center gap-2">
                  {user?.profile_picture ? (
                    <img 
                      src={user.profile_picture} 
                      alt={user.full_name || 'User'} 
                      className="h-8 w-8 rounded-full object-cover flex-shrink-0" 
                    />
                  ) : (
                    <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs flex-shrink-0">
                      {user?.full_name?.charAt(0).toUpperCase() || 'U'}
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-slate-800 truncate leading-tight">{user?.full_name}</p>
                    <p className="text-[10px] text-slate-500 truncate leading-normal mt-0.5">{user?.email}</p>
                  </div>
                </div>
                <Link 
                  href="/dashboard/settings/profile"
                  onClick={() => setIsDropdownOpen(false)}
                  className="flex w-full items-center px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  <UserIcon className="mr-2 h-4 w-4" />
                  Your Profile
                </Link>
                <button 
                  onClick={handleLogout}
                  className="flex w-full items-center px-4 py-2 text-sm text-destructive hover:bg-red-50 transition-colors"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
