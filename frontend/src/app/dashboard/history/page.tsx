'use client'

import { useState } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import {
  usePatientConsultations,
  usePatientPrescriptions,
} from '@/hooks/use-prescriptions'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import {
  Stethoscope,
  Pill,
  Search,
  Calendar,
  FileText,
  User,
  Activity,
  ClipboardList,
  Eye,
  ChevronRight,
  Clock,
} from 'lucide-react'
import { PatientConsultationItem, PatientPrescription } from '@/types'

export default function PatientHistoryPage() {
  return (
    <ProtectedRoute allowedRoles={['patient']}>
      <PatientHistoryContent />
    </ProtectedRoute>
  )
}

function PatientHistoryContent() {
  const { data: consultations, isLoading: loadingConsultations } = usePatientConsultations()
  const { data: prescriptions, isLoading: loadingPrescriptions } = usePatientPrescriptions()

  const [activeTab, setActiveTab] = useState<'consultations' | 'prescriptions'>('consultations')
  const [searchTerm, setSearchTerm] = useState('')

  // Modal control states
  const [isConsultationModalOpen, setIsConsultationModalOpen] = useState(false)
  const [selectedConsultation, setSelectedConsultation] = useState<PatientConsultationItem | null>(null)

  const [isPrescriptionModalOpen, setIsPrescriptionModalOpen] = useState(false)
  const [selectedPrescription, setSelectedPrescription] = useState<PatientPrescription | null>(null)

  // Map of prescriptions for quick lookup from consultation details
  const prescriptionMap = new Map(prescriptions?.map((p) => [p.id, p]) ?? [])

  // Filter handlers
  const filteredConsultations = consultations?.filter((c) => {
    const doctorName = c.doctor_name?.toLowerCase() ?? 'unknown'
    const diagnosis = c.diagnosis?.toLowerCase() ?? 'unknown'
    const specialization = c.doctor_specialization?.toLowerCase() ?? 'unknown'
    const query = searchTerm.toLowerCase()
    return doctorName.includes(query) || diagnosis.includes(query) || specialization.includes(query)
  }) ?? []

  const filteredPrescriptions = prescriptions?.filter((p) => {
    const doctorName = p.doctor_name?.toLowerCase() ?? 'unknown'
    const diagnosis = p.diagnosis?.toLowerCase() ?? 'unknown'
    const drugNames = p.medications.map((m) => m.drug_name.toLowerCase()).join(' ')
    const query = searchTerm.toLowerCase()
    return doctorName.includes(query) || diagnosis.includes(query) || drugNames.includes(query)
  }) ?? []

  const openConsultationModal = (consultation: PatientConsultationItem) => {
    setSelectedConsultation(consultation)
    setIsConsultationModalOpen(true)
  }

  const openPrescriptionModal = (prescription: PatientPrescription) => {
    setSelectedPrescription(prescription)
    setIsPrescriptionModalOpen(true)
  }

  const openPrescriptionFromConsultation = (prescriptionId: string) => {
    const rx = prescriptions?.find((p) => p.id === prescriptionId)
    if (rx) {
      setIsConsultationModalOpen(false)
      setSelectedPrescription(rx)
      setIsPrescriptionModalOpen(true)
    }
  }

  const isLoading = loadingConsultations || loadingPrescriptions

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Medical History</h1>
          <p className="text-slate-500">
            View your consultation history and prescriptions issued by Nura doctors.
          </p>
        </div>
      </div>

      {/* Tabs Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex gap-2 p-1 bg-slate-100 rounded-lg w-fit">
          <Button
            variant={activeTab === 'consultations' ? 'default' : 'ghost'}
            className={activeTab === 'consultations' ? 'bg-teal-600 hover:bg-teal-700' : 'text-slate-600'}
            onClick={() => {
              setActiveTab('consultations')
              setSearchTerm('')
            }}
          >
            Consultations ({consultations?.length ?? 0})
          </Button>
          <Button
            variant={activeTab === 'prescriptions' ? 'default' : 'ghost'}
            className={activeTab === 'prescriptions' ? 'bg-teal-600 hover:bg-teal-700' : 'text-slate-600'}
            onClick={() => {
              setActiveTab('prescriptions')
              setSearchTerm('')
            }}
          >
            Prescriptions ({prescriptions?.length ?? 0})
          </Button>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            placeholder={activeTab === 'consultations' ? 'Search by doctor or diagnosis...' : 'Search by doctor, diagnosis or drug...'}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9 border-slate-200"
          />
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-28 bg-slate-100 rounded-lg animate-pulse" />
          ))}
        </div>
      )}

      {/* Empty States */}
      {!isLoading && activeTab === 'consultations' && filteredConsultations.length === 0 && (
        <Card className="border-dashed border-slate-300 py-12 flex flex-col items-center justify-center text-center">
          <Stethoscope className="h-10 w-10 text-slate-300 mb-3" />
          <h3 className="text-md font-semibold text-slate-700">No consultations found</h3>
          <p className="text-sm text-slate-400 max-w-sm mt-1">
            {searchTerm ? 'Try adjusting your search query.' : 'Book an appointment to begin your care journey with a Nura doctor.'}
          </p>
        </Card>
      )}

      {!isLoading && activeTab === 'prescriptions' && filteredPrescriptions.length === 0 && (
        <Card className="border-dashed border-slate-300 py-12 flex flex-col items-center justify-center text-center">
          <Pill className="h-10 w-10 text-slate-300 mb-3" />
          <h3 className="text-md font-semibold text-slate-700">No prescriptions found</h3>
          <p className="text-sm text-slate-400 max-w-sm mt-1">
            {searchTerm ? 'No prescriptions match your search criteria.' : 'Your active prescriptions issued by doctors will appear here.'}
          </p>
        </Card>
      )}

      {/* Consultations List */}
      {!isLoading && activeTab === 'consultations' && filteredConsultations.length > 0 && (
        <div className="space-y-4">
          {filteredConsultations.map((c) => (
            <Card
              key={c.id}
              className="border-slate-200 shadow-sm hover:shadow-md transition-shadow hover:border-teal-100 cursor-pointer"
              onClick={() => openConsultationModal(c)}
            >
              <CardContent className="p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="flex gap-4">
                  <div className="p-3 bg-teal-50 text-teal-600 rounded-xl h-fit">
                    <Stethoscope className="h-6 w-6" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold text-slate-800 text-base">{c.doctor_name}</h3>
                      <span className="text-xs px-2 py-0.5 bg-teal-50 text-teal-600 rounded">
                        {c.doctor_specialization}
                      </span>
                    </div>
                    <div className="flex items-center text-xs text-slate-400 gap-1">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>{new Date(c.appointment_date + 'T' + c.appointment_time).toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <p className="text-sm text-slate-600 font-semibold pt-1">
                      Diagnosis: <span className="text-slate-800">{c.diagnosis}</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end border-t sm:border-0 pt-3 sm:pt-0">
                  <div className="flex items-center gap-2">
                    {c.prescription_status === 'Prescribed' ? (
                      <span className="text-xs font-semibold px-2 py-0.5 bg-emerald-50 text-emerald-600 rounded flex items-center gap-1 border border-emerald-100">
                        <Pill className="h-3 w-3" />
                        Prescribed
                      </span>
                    ) : (
                      <span className="text-xs font-medium px-2 py-0.5 bg-slate-50 text-slate-500 rounded border border-slate-100">
                        No Prescription
                      </span>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-teal-600 hover:text-teal-700 hover:bg-teal-50 flex items-center gap-1 text-xs"
                  >
                    View Details
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Prescriptions List */}
      {!isLoading && activeTab === 'prescriptions' && filteredPrescriptions.length > 0 && (
        <div className="space-y-4">
          {filteredPrescriptions.map((p) => (
            <Card
              key={p.id}
              className="border-slate-200 shadow-sm hover:shadow-md transition-shadow hover:border-emerald-100 cursor-pointer"
              onClick={() => openPrescriptionModal(p)}
            >
              <CardContent className="p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="flex gap-4">
                  <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl h-fit">
                    <Pill className="h-6 w-6" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold text-slate-800 text-base">{p.doctor_name}</h3>
                      <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
                        {p.doctor_specialization}
                      </span>
                    </div>
                    <div className="flex items-center text-xs text-slate-400 gap-1">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>Issued: {new Date(p.created_at).toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })}</span>
                    </div>
                    <p className="text-sm text-slate-700 pt-1 flex items-center gap-1.5">
                      <ClipboardList className="h-4 w-4 text-slate-400" />
                      <span className="font-semibold">{p.medications.length} medication{p.medications.length !== 1 ? 's' : ''}</span>
                      <span className="text-slate-400">·</span>
                      <span className="text-xs text-slate-500 italic">Diagnosis: {p.diagnosis}</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end border-t sm:border-0 pt-3 sm:pt-0">
                  <span className="text-xs font-semibold px-2 py-0.5 bg-blue-50 text-blue-600 rounded border border-blue-100">
                    Active
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 flex items-center gap-1 text-xs"
                  >
                    View Rx
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Consultation Details Modal */}
      <Dialog open={isConsultationModalOpen} onOpenChange={setIsConsultationModalOpen}>
        <DialogContent className="max-w-xl max-h-[85vh] overflow-y-auto">
          {selectedConsultation && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Stethoscope className="h-5 w-5 text-teal-600" />
                  <span>Consultation Details</span>
                </DialogTitle>
                <DialogDescription>
                  Record from your visit with {selectedConsultation.doctor_name}.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-5 py-3">
                {/* Doctor and Date Section */}
                <div className="flex flex-col sm:flex-row justify-between border-b pb-3.5 gap-3">
                  <div>
                    <h4 className="font-bold text-slate-800 text-lg">{selectedConsultation.doctor_name}</h4>
                    <p className="text-sm text-slate-500">{selectedConsultation.doctor_specialization}</p>
                  </div>
                  <div className="flex sm:flex-col items-start sm:items-end justify-between sm:justify-start gap-1">
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5" />
                      {new Date(selectedConsultation.appointment_date + 'T' + selectedConsultation.appointment_time).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                    </span>
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" />
                      {selectedConsultation.appointment_time}
                    </span>
                  </div>
                </div>

                {/* Diagnosis Section */}
                <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Diagnosis
                  </span>
                  <p className="text-base font-semibold text-slate-800">{selectedConsultation.diagnosis}</p>
                </div>

                {/* Clinical Notes Section */}
                <div className="space-y-1">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                    Doctor Notes
                  </span>
                  <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                    {selectedConsultation.consultation_notes}
                  </p>
                </div>

                {/* Follow-up Section */}
                <div className="border-t pt-3.5 space-y-1">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                    Follow-up Schedule
                  </span>
                  {selectedConsultation.follow_up_required ? (
                    <p className="text-sm text-slate-800 font-medium">
                      Yes, scheduled for:{' '}
                      <span className="text-teal-600 font-semibold">
                        {selectedConsultation.follow_up_date
                          ? new Date(selectedConsultation.follow_up_date).toLocaleDateString(undefined, {
                              month: 'long',
                              day: 'numeric',
                              year: 'numeric',
                            })
                          : 'TBD'}
                      </span>
                    </p>
                  ) : (
                    <p className="text-sm text-slate-500">No immediate follow-up required.</p>
                  )}
                </div>

                {/* Attached Prescription Section */}
                {selectedConsultation.prescription_id && (
                  <div className="bg-emerald-50/50 p-4 rounded-lg border border-emerald-100 flex items-center justify-between mt-2">
                    <div className="flex gap-3 items-center">
                      <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg">
                        <Pill className="h-5 w-5" />
                      </div>
                      <div>
                        <h5 className="text-sm font-semibold text-slate-800">Prescription Attached</h5>
                        <p className="text-xs text-slate-500">Issued during this consultation</p>
                      </div>
                    </div>
                    <Button
                      onClick={() => openPrescriptionFromConsultation(selectedConsultation.prescription_id!)}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs h-9 px-4 flex items-center gap-1 font-semibold"
                    >
                      <Eye className="h-3.5 w-3.5" />
                      View Rx
                    </Button>
                  </div>
                )}
              </div>

              <DialogFooter>
                <Button
                  onClick={() => setIsConsultationModalOpen(false)}
                  className="bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm w-full sm:w-auto h-10"
                >
                  Close Record
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Prescription Details Modal */}
      <Dialog open={isPrescriptionModalOpen} onOpenChange={setIsPrescriptionModalOpen}>
        <DialogContent className="max-w-xl max-h-[85vh] overflow-y-auto">
          {selectedPrescription && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Pill className="h-5 w-5 text-emerald-600" />
                  <span>Prescription Details</span>
                </DialogTitle>
                <DialogDescription>
                  Issued by Dr. {selectedPrescription.doctor_name} for diagnosis: {selectedPrescription.diagnosis}.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-5 py-3">
                {/* Doctor and Date Details */}
                <div className="flex justify-between border-b pb-3.5">
                  <div>
                    <h4 className="font-bold text-slate-800 text-lg">{selectedPrescription.doctor_name}</h4>
                    <p className="text-sm text-slate-500">{selectedPrescription.doctor_specialization}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400 block">
                      Date Issued:
                    </span>
                    <span className="text-sm font-semibold text-slate-800">
                      {new Date(selectedPrescription.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                    </span>
                  </div>
                </div>

                {/* Medications List */}
                <div className="space-y-3">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                    Prescribed Medications
                  </span>
                  <div className="space-y-3">
                    {selectedPrescription.medications.map((m, index) => (
                      <div
                        key={index}
                        className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/60 flex items-start justify-between"
                      >
                        <div className="space-y-1">
                          <h5 className="font-bold text-slate-800 text-sm">{m.drug_name}</h5>
                          <div className="flex flex-wrap gap-x-2.5 text-xs text-slate-500 font-semibold">
                            <span>Dosage: {m.dosage}</span>
                            <span>·</span>
                            <span>Frequency: {m.frequency}</span>
                            <span>·</span>
                            <span>Duration: {m.duration}</span>
                          </div>
                          {m.instructions && (
                            <p className="text-xs text-slate-500 italic mt-1 font-semibold">
                              Instructions: {m.instructions}
                            </p>
                          )}
                        </div>
                        <div className="p-1 bg-emerald-50 rounded text-emerald-600">
                          <Pill className="h-4 w-4" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Additional dosage instructions */}
                {selectedPrescription.dosage_instructions && (
                  <div className="space-y-1">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                      Dosage Instructions
                    </span>
                    <p className="text-sm text-slate-700 leading-relaxed bg-slate-50/50 p-3 rounded-lg border border-slate-100">
                      {selectedPrescription.dosage_instructions}
                    </p>
                  </div>
                )}

                {/* Notes */}
                {selectedPrescription.notes && (
                  <div className="space-y-1">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                      General Notes
                    </span>
                    <p className="text-sm text-slate-600 leading-relaxed">
                      {selectedPrescription.notes}
                    </p>
                  </div>
                )}
              </div>

              <DialogFooter>
                <Button
                  onClick={() => setIsPrescriptionModalOpen(false)}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm w-full sm:w-auto h-10"
                >
                  Close Prescription
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
