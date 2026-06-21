'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { userService, NotificationPreferences } from '@/services/user.service'

import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { useState, useEffect } from 'react'

export default function PreferencesSettingsPage() {
  const queryClient = useQueryClient()
  
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['userPreferences'],
    queryFn: userService.getPreferences,
  })

  const [toggles, setToggles] = useState<Partial<NotificationPreferences>>({
    email_enabled: true,
    appointment_enabled: true,
    reminder_enabled: true,
    report_enabled: true,
    marketing_enabled: false,
  })
  
  const [isDirty, setIsDirty] = useState(false)

  useEffect(() => {
    if (preferences) {
      setToggles({
        email_enabled: preferences.email_enabled,
        appointment_enabled: preferences.appointment_enabled,
        reminder_enabled: preferences.reminder_enabled,
        report_enabled: preferences.report_enabled,
        marketing_enabled: preferences.marketing_enabled,
      })
      setIsDirty(false)
    }
  }, [preferences])

  const updateMutation = useMutation({
    mutationFn: userService.updatePreferences,
    onSuccess: (data) => {
      queryClient.setQueryData(['userPreferences'], data)
      toast.success('Preferences updated successfully')
      setIsDirty(false)
    },
    onError: (error: any) => {
      toast.error(error?.message || 'Failed to update preferences')
    }
  })

  const handleToggle = (key: keyof NotificationPreferences) => {
    setToggles(prev => {
      const next = { ...prev, [key]: !prev[key as keyof typeof prev] }
      setIsDirty(true)
      return next
    })
  }

  const handleSave = () => {
    updateMutation.mutate(toggles)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-10">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Notification Preferences</h3>
        <p className="text-sm text-muted-foreground">
          Choose what you want to be notified about.
        </p>
      </div>
      <div className="border-t border-slate-200"></div>
      
      <div className="space-y-6">
        {/* Email Notifications */}
        <div className="flex items-center justify-between rounded-lg border p-4">
          <div className="space-y-0.5">
            <Label className="text-base">Email Notifications</Label>
            <p className="text-sm text-muted-foreground">
              Receive notifications via email.
            </p>
          </div>
          <div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                className="sr-only peer"
                checked={toggles.email_enabled}
                onChange={() => handleToggle('email_enabled')}
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        </div>

        {/* Appointment Updates */}
        <div className="flex items-center justify-between rounded-lg border p-4">
          <div className="space-y-0.5">
            <Label className="text-base">Appointment Updates</Label>
            <p className="text-sm text-muted-foreground">
              Get notified when appointments are approved, cancelled, or nearing.
            </p>
          </div>
          <div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                className="sr-only peer"
                checked={toggles.appointment_enabled}
                onChange={() => handleToggle('appointment_enabled')}
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        </div>

        {/* Medication Reminders */}
        <div className="flex items-center justify-between rounded-lg border p-4">
          <div className="space-y-0.5">
            <Label className="text-base">Health Reminders</Label>
            <p className="text-sm text-muted-foreground">
              Daily medication and habit reminders.
            </p>
          </div>
          <div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                className="sr-only peer"
                checked={toggles.reminder_enabled}
                onChange={() => handleToggle('reminder_enabled')}
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        </div>

        {/* Report Updates */}
        <div className="flex items-center justify-between rounded-lg border p-4">
          <div className="space-y-0.5">
            <Label className="text-base">Report Analysis</Label>
            <p className="text-sm text-muted-foreground">
              Get notified when your medical reports are fully analyzed by AI.
            </p>
          </div>
          <div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                className="sr-only peer"
                checked={toggles.report_enabled}
                onChange={() => handleToggle('report_enabled')}
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        </div>

        {/* Marketing */}
        <div className="flex items-center justify-between rounded-lg border p-4">
          <div className="space-y-0.5">
            <Label className="text-base">Marketing Emails</Label>
            <p className="text-sm text-muted-foreground">
              Receive updates about new features and offers.
            </p>
          </div>
          <div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                className="sr-only peer"
                checked={toggles.marketing_enabled}
                onChange={() => handleToggle('marketing_enabled')}
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        </div>

        <Button 
          onClick={handleSave} 
          disabled={updateMutation.isPending || !isDirty}
        >
          {updateMutation.isPending ? 'Saving...' : 'Save preferences'}
        </Button>
      </div>
    </div>
  )
}
