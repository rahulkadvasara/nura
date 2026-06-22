'use client'

import { useState } from 'react'
import Link from 'next/link'
import { 
  Search, 
  Stethoscope, 
  Clock, 
  MapPin, 
  Languages, 
  Star, 
  DollarSign, 
  Filter, 
  X, 
  ChevronRight,
  User,
  GraduationCap
} from 'lucide-react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { useDoctors } from '@/hooks/use-doctor-discovery'

const COMMON_SPECIALIZATIONS = [
  'All Specializations',
  'Cardiology',
  'Dermatology',
  'Pediatrics',
  'General Medicine',
  'Orthopedics',
  'Neurology',
  'Gynecology',
  'Psychiatry',
  'Ophthalmology'
]

function DoctorDirectoryContent() {
  const [searchTerm, setSearchTerm] = useState('')
  const [specialization, setSpecialization] = useState('')
  const [minExperience, setMinExperience] = useState<number | undefined>(undefined)

  const { data, isLoading, isError, error, refetch } = useDoctors({
    search: searchTerm || undefined,
    specialization: specialization === 'All Specializations' || !specialization ? undefined : specialization,
    min_experience: minExperience || undefined
  })

  const resetFilters = () => {
    setSearchTerm('')
    setSpecialization('')
    setMinExperience(undefined)
  }

  const doctorsList = data?.doctors || []

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Title Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Find a Doctor</h1>
        <p className="text-slate-500 mt-1">Browse verified medical practitioners and book consultations.</p>
      </div>

      {/* Filter and Search Bar Card */}
      <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
        <CardContent className="p-4 md:p-6 space-y-4">
          <div className="flex flex-col md:flex-row gap-3">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <Input
                type="text"
                placeholder="Search by doctor name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 bg-slate-50/50 border-slate-200 focus:bg-white transition-colors"
              />
            </div>

            {/* Specialization Select */}
            <div className="w-full md:w-64">
              <select
                value={specialization}
                onChange={(e) => setSpecialization(e.target.value)}
                className="flex h-10 w-full rounded-md border border-slate-200 bg-slate-50/50 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-600 focus:bg-white transition-colors"
              >
                <option value="">Select Specialization</option>
                {COMMON_SPECIALIZATIONS.map((spec) => (
                  <option key={spec} value={spec}>
                    {spec}
                  </option>
                ))}
              </select>
            </div>

            {/* Experience Selection Dropdown */}
            <div className="w-full md:w-56">
              <select
                value={minExperience === undefined ? '' : minExperience.toString()}
                onChange={(e) => setMinExperience(e.target.value ? parseInt(e.target.value) : undefined)}
                className="flex h-10 w-full rounded-md border border-slate-200 bg-slate-50/50 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-600 focus:bg-white transition-colors"
              >
                <option value="">Any Experience</option>
                <option value="3">3+ Years of Experience</option>
                <option value="5">5+ Years of Experience</option>
                <option value="10">10+ Years of Experience</option>
                <option value="15">15+ Years of Experience</option>
              </select>
            </div>

            {/* Reset Button */}
            {(searchTerm || specialization || minExperience !== undefined) && (
              <Button
                variant="outline"
                onClick={resetFilters}
                className="border-slate-200 text-slate-500 hover:text-slate-700 flex items-center gap-1.5 shrink-0"
              >
                <X className="h-4 w-4" />
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Loading Skeleton Grid */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-[280px] bg-white border border-slate-200 rounded-xl animate-pulse"
            />
          ))}
        </div>
      )}

      {/* Error View */}
      {isError && (
        <div className="flex flex-col items-center justify-center py-16 text-center bg-white border rounded-xl">
          <div className="p-4 rounded-full bg-rose-50 mb-4">
            <Stethoscope className="h-8 w-8 text-rose-500" />
          </div>
          <h3 className="text-lg font-semibold text-slate-800 mb-1">
            Failed to search doctors
          </h3>
          <p className="text-sm text-slate-500 mb-5 max-w-md">
            {error?.message || 'Something went wrong while retrieving the doctor directory.'}
          </p>
          <Button onClick={() => refetch()} variant="outline" className="border-slate-300">
            Retry
          </Button>
        </div>
      )}

      {/* Empty States */}
      {!isLoading && !isError && doctorsList.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center bg-white border border-dashed rounded-xl p-8">
          <div className="p-4 rounded-full bg-slate-50 mb-4 text-slate-400">
            <Search className="h-8 w-8" />
          </div>
          <h3 className="text-lg font-semibold text-slate-800 mb-1">
            No doctors found
          </h3>
          <p className="text-sm text-slate-500 mb-5 max-w-md">
            We couldn&apos;t find any verified doctors matching your search parameters. Try adjusting your query or specialization filters.
          </p>
          <Button onClick={resetFilters} className="bg-teal-600 hover:bg-teal-700 text-white">
            Reset All Filters
          </Button>
        </div>
      )}

      {/* Doctor Cards Grid */}
      {!isLoading && !isError && doctorsList.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {doctorsList.map((doc) => (
            <Card key={doc.id} className="border-slate-200 hover:border-teal-500/50 hover:shadow-md transition-all duration-300 flex flex-col bg-white overflow-hidden group">
              <CardContent className="p-5 flex-1 flex flex-col justify-between">
                <div>
                  {/* Doctor Profile Pic and Basic Credentials */}
                  <div className="flex items-start gap-4">
                    {doc.profile_picture ? (
                      <img
                        src={doc.profile_picture}
                        alt={doc.name}
                        className="h-14 w-14 rounded-xl object-cover border border-slate-100 group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <div className="h-14 w-14 rounded-xl bg-teal-50 border border-teal-100/50 text-teal-600 flex items-center justify-center shrink-0">
                        <User className="h-6 w-6" />
                      </div>
                    )}
                    <div className="space-y-1">
                      <h3 className="font-bold text-slate-900 group-hover:text-teal-600 transition-colors">
                        {doc.name.toLowerCase().startsWith('dr.') ? doc.name : `Dr. ${doc.name}`}
                      </h3>
                      <Badge className="bg-teal-50 text-teal-700 hover:bg-teal-100/50 border-teal-100/30 text-xs font-semibold py-0.5 px-2.5">
                        {doc.specialization}
                      </Badge>
                    </div>
                  </div>

                  {/* Rating indicator */}
                  <div className="flex items-center gap-1 mt-4 text-xs text-slate-500">
                    <div className="flex items-center text-amber-500">
                      <Star className="h-3.5 w-3.5 fill-current" />
                      <span className="font-bold text-slate-700 ml-1">
                        {doc.average_rating > 0 ? doc.average_rating.toFixed(1) : 'New'}
                      </span>
                    </div>
                    <span>•</span>
                    <span>{doc.total_reviews} Reviews</span>
                  </div>

                  {/* Experience, Education details */}
                  <div className="mt-4 space-y-2 text-xs text-slate-500 leading-normal border-t border-slate-50 pt-4">
                    <div className="flex items-center gap-2">
                      <Clock className="h-3.5 w-3.5 text-slate-400" />
                      <span>{doc.experience_years} Years of Experience</span>
                    </div>
                    {doc.education && (
                      <div className="flex items-center gap-2">
                        <GraduationCap className="h-3.5 w-3.5 text-slate-400" />
                        <span className="truncate max-w-[220px]">{doc.education}</span>
                      </div>
                    )}
                    {doc.hospital && (
                      <div className="flex items-center gap-2">
                        <MapPin className="h-3.5 w-3.5 text-slate-400" />
                        <span className="truncate max-w-[220px]">{doc.hospital}</span>
                      </div>
                    )}
                    {doc.languages && doc.languages.length > 0 && (
                      <div className="flex items-center gap-2">
                        <Languages className="h-3.5 w-3.5 text-slate-400" />
                        <span className="truncate max-w-[220px]">{doc.languages.join(', ')}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Bottom line: fee and view button */}
                <div className="flex items-center justify-between border-t border-slate-50 mt-4 pt-4 shrink-0">
                  <div>
                    <span className="text-[10px] text-slate-400 block font-semibold uppercase tracking-wider">Cons. Fee</span>
                    <span className="text-base font-bold text-slate-900 flex items-center">
                      ₹{doc.consultation_fee}
                    </span>
                  </div>
                  <Link href={`/dashboard/doctors/${doc.id}`}>
                    <Button className="bg-teal-600 hover:bg-teal-700 text-white text-xs py-1.5 px-3.5 h-8 flex items-center gap-1">
                      View Profile
                      <ChevronRight className="h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

export default function DoctorDirectoryPage() {
  return (
    <ProtectedRoute allowedRoles={['patient']}>
      <DoctorDirectoryContent />
    </ProtectedRoute>
  )
}
