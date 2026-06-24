'use client'

import { useState } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import {
  useCreatePrescription,
  useUpdatePrescription,
  useDoctorPrescriptions,
} from '@/hooks/use-prescriptions'
import { useDoctorConsultations } from '@/hooks/use-appointments'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import {
  Pill,
  Plus,
  Trash2,
  Edit,
  Search,
  FileText,
  User,
  Calendar,
  AlertCircle,
  ClipboardList,
} from 'lucide-react'
import { Medication } from '@/types'
import { toast } from 'sonner'

export default function DoctorPrescriptionsPage() {
  return (
    <ProtectedRoute allowedRoles={['doctor']}>
      <DoctorPrescriptionsContent />
    </ProtectedRoute>
  )
}

function DoctorPrescriptionsContent() {
  const queryClient = useDoctorPrescriptions()
  const { data: prescriptions, isLoading: loadingPrescriptions, refetch: refetchPrescriptions } = useDoctorPrescriptions()
  const { data: consultations, isLoading: loadingConsultations } = useDoctorConsultations()

  const createPrescriptionMutation = useCreatePrescription()
  const updatePrescriptionMutation = useUpdatePrescription()

  const [activeTab, setActiveTab] = useState<'list' | 'pending'>('list')
  const [searchTerm, setSearchTerm] = useState('')

  // Modal control states
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedConsultationId, setSelectedConsultationId] = useState<string | null>(null)
  const [selectedPrescriptionId, setSelectedPrescriptionId] = useState<string | null>(null)

  // Form states
  const [medications, setMedications] = useState<Medication[]>([
    { drug_name: '', dosage: '', frequency: '', duration: '', instructions: '' },
  ])
  const [dosageInstructions, setDosageInstructions] = useState('')
  const [notes, setNotes] = useState('')

  // Map of consultations for quick lookup
  const consultationMap = new Map(consultations?.map((c) => [c.id, c]) ?? [])

  // Prescribed consultation IDs Set
  const prescribedConsultationIds = new Set(prescriptions?.map((p) => p.consultation_id) ?? [])

  // Consultations waiting for a prescription
  const pendingConsultations = consultations?.filter((c) => !prescribedConsultationIds.has(c.id)) ?? []

  // Filtered lists
  const filteredPrescriptions = prescriptions?.filter((p) => {
    const consultation = consultationMap.get(p.consultation_id)
    const patientName = consultation?.patient_name?.toLowerCase() ?? 'unknown'
    const drugNames = p.medications.map((m) => m.drug_name.toLowerCase()).join(' ')
    const query = searchTerm.toLowerCase()
    return patientName.includes(query) || drugNames.includes(query)
  }) ?? []

  const filteredPending = pendingConsultations.filter((c) => {
    const patientName = c.patient_name?.toLowerCase() ?? 'unknown'
    const diagnosis = c.diagnosis?.toLowerCase() ?? 'unknown'
    const query = searchTerm.toLowerCase()
    return patientName.includes(query) || diagnosis.includes(query)
  })

  // Medication handlers
  const handleMedicationChange = (index: number, field: keyof Medication, value: string) => {
    const updated = [...medications]
    updated[index] = { ...updated[index], [field]: value }
    setMedications(updated)
  }

  const addMedicationRow = () => {
    setMedications([
      ...medications,
      { drug_name: '', dosage: '', frequency: '', duration: '', instructions: '' },
    ])
  }

  const removeMedicationRow = (index: number) => {
    if (medications.length === 1) {
      toast.warning('A prescription must contain at least one medication.')
      return
    }
    setMedications(medications.filter((_, i) => i !== index))
  }

  // Open modal for writing a new prescription
  const openCreateModal = (consultationId: string) => {
    setModalMode('create')
    setSelectedConsultationId(consultationId)
    setMedications([{ drug_name: '', dosage: '', frequency: '', duration: '', instructions: '' }])
    setDosageInstructions('')
    setNotes('')
    setIsModalOpen(true)
  }

  // Open modal for editing a prescription
  const openEditModal = (prescriptionId: string) => {
    const prescription = prescriptions?.find((p) => p.id === prescriptionId)
    if (!prescription) return

    setModalMode('edit')
    setSelectedPrescriptionId(prescriptionId)
    setSelectedConsultationId(prescription.consultation_id)
    setMedications(
      prescription.medications.map((m) => ({
        drug_name: m.drug_name,
        dosage: m.dosage,
        frequency: m.frequency,
        duration: m.duration,
        instructions: m.instructions ?? '',
      }))
    )
    setDosageInstructions(prescription.dosage_instructions ?? '')
    setNotes(prescription.notes ?? '')
    setIsModalOpen(true)
  }

  // Form submission handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Validation
    const invalidMed = medications.some(
      (m) => !m.drug_name.trim() || !m.dosage.trim() || !m.frequency.trim() || !m.duration.trim()
    )
    if (invalidMed) {
      toast.error('Please fill in all medication fields (Drug Name, Dosage, Frequency, Duration).')
      return
    }

    try {
      if (modalMode === 'create' && selectedConsultationId) {
        await createPrescriptionMutation.mutateAsync({
          consultationId: selectedConsultationId,
          payload: {
            medications,
            dosage_instructions: dosageInstructions.trim() || undefined,
            notes: notes.trim() || undefined,
          },
        })
        toast.success('Prescription created and sent to patient successfully!')
      } else if (modalMode === 'edit' && selectedPrescriptionId) {
        await updatePrescriptionMutation.mutateAsync({
          prescriptionId: selectedPrescriptionId,
          payload: {
            medications,
            dosage_instructions: dosageInstructions.trim() || undefined,
            notes: notes.trim() || undefined,
          },
        })
        toast.success('Prescription updated successfully!')
      }
      setIsModalOpen(false)
      refetchPrescriptions()
    } catch (err: any) {
      toast.error(err.message || 'An error occurred while saving the prescription.')
    }
  }

  const isLoading = loadingPrescriptions || loadingConsultations

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Prescription Center</h1>
          <p className="text-slate-500">
            Write, review, and manage prescriptions for your patients.
          </p>
        </div>
      </div>

      {/* Tabs Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex gap-2 p-1 bg-slate-100 rounded-lg w-fit">
          <Button
            variant={activeTab === 'list' ? 'default' : 'ghost'}
            className={activeTab === 'list' ? 'bg-teal-600 hover:bg-teal-700' : 'text-slate-600'}
            onClick={() => {
              setActiveTab('list')
              setSearchTerm('')
            }}
          >
            Recent Prescriptions ({prescriptions?.length ?? 0})
          </Button>
          <Button
            variant={activeTab === 'pending' ? 'default' : 'ghost'}
            className={activeTab === 'pending' ? 'bg-teal-600 hover:bg-teal-700' : 'text-slate-600'}
            onClick={() => {
              setActiveTab('pending')
              setSearchTerm('')
            }}
          >
            Pending Prescriptions ({pendingConsultations.length})
          </Button>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            placeholder={activeTab === 'list' ? 'Search by patient or drug...' : 'Search by patient or diagnosis...'}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9 border-slate-200"
          />
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-44 bg-slate-100 rounded-lg animate-pulse" />
          ))}
        </div>
      )}

      {/* Empty States */}
      {!isLoading && activeTab === 'list' && filteredPrescriptions.length === 0 && (
        <Card className="border-dashed border-slate-300 py-12 flex flex-col items-center justify-center text-center">
          <Pill className="h-10 w-10 text-slate-300 mb-3" />
          <h3 className="text-md font-semibold text-slate-700">No prescriptions found</h3>
          <p className="text-sm text-slate-400 max-w-sm mt-1">
            {searchTerm ? 'Try adjusting your search criteria.' : 'Go to the pending tab to issue prescriptions for recent consultations.'}
          </p>
          {!searchTerm && pendingConsultations.length > 0 && (
            <Button
              className="mt-4 bg-teal-600 hover:bg-teal-700"
              onClick={() => setActiveTab('pending')}
            >
              View Pending Consultations
            </Button>
          )}
        </Card>
      )}

      {!isLoading && activeTab === 'pending' && filteredPending.length === 0 && (
        <Card className="border-dashed border-slate-300 py-12 flex flex-col items-center justify-center text-center">
          <ClipboardList className="h-10 w-10 text-slate-300 mb-3" />
          <h3 className="text-md font-semibold text-slate-700">All caught up!</h3>
          <p className="text-sm text-slate-400 max-w-sm mt-1">
            {searchTerm ? 'No pending consultations match your search.' : 'You have written prescriptions for all completed consultations.'}
          </p>
        </Card>
      )}

      {/* Grid Lists */}
      {!isLoading && activeTab === 'list' && filteredPrescriptions.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPrescriptions.map((p) => {
            const consultation = consultationMap.get(p.consultation_id)
            return (
              <Card key={p.id} className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="p-4 border-b">
                  <div className="flex justify-between items-start">
                    <div className="flex gap-2 items-center">
                      <div className="p-1.5 bg-emerald-50 rounded-lg text-emerald-600">
                        <Pill className="h-4.5 w-4.5" />
                      </div>
                      <div>
                        <CardTitle className="text-sm font-semibold text-slate-800">
                          {consultation?.patient_name || 'Patient'}
                        </CardTitle>
                        <CardDescription className="text-xs">
                          {consultation ? `Diagnosis: ${consultation.diagnosis}` : 'Completed Consultation'}
                        </CardDescription>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openEditModal(p.id)}
                      className="h-8 text-xs border-slate-200 hover:bg-slate-50 flex items-center gap-1"
                    >
                      <Edit className="h-3 w-3" />
                      Edit
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-3">
                  <div>
                    <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                      Medications ({p.medications.length})
                    </h5>
                    <ul className="space-y-1.5">
                      {p.medications.slice(0, 3).map((med, index) => (
                        <li key={index} className="text-xs text-slate-700 flex items-center justify-between">
                          <span className="font-semibold text-slate-800">{med.drug_name}</span>
                          <span className="text-slate-500">
                            {med.dosage} · {med.frequency}
                          </span>
                        </li>
                      ))}
                      {p.medications.length > 3 && (
                        <li className="text-xs text-teal-600 font-semibold mt-1">
                          + {p.medications.length - 3} more medications
                        </li>
                      )}
                    </ul>
                  </div>

                  <div className="flex items-center text-xs text-slate-400 justify-between pt-2 border-t">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>{new Date(p.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {!isLoading && activeTab === 'pending' && filteredPending.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPending.map((c) => (
            <Card key={c.id} className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
              <CardHeader className="p-4 border-b bg-slate-50/50">
                <div className="flex justify-between items-start">
                  <div className="flex gap-2 items-center">
                    <div className="p-1.5 bg-slate-100 rounded-lg text-slate-600">
                      <User className="h-4.5 w-4.5" />
                    </div>
                    <div>
                      <CardTitle className="text-sm font-semibold text-slate-800">
                        {c.patient_name}
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Completed: {new Date(c.created_at).toLocaleDateString()}
                      </CardDescription>
                    </div>
                  </div>
                  <Button
                    onClick={() => openCreateModal(c.id)}
                    className="h-8 text-xs bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-1"
                  >
                    <Plus className="h-3 w-3" />
                    Prescribe
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-4 space-y-3">
                <div className="bg-white p-2.5 rounded border border-slate-100">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-0.5">
                    Diagnosis
                  </span>
                  <p className="text-xs text-slate-800 font-semibold">{c.diagnosis}</p>
                </div>
                <div className="bg-white p-2.5 rounded border border-slate-100">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-0.5">
                    Clinical Notes
                  </span>
                  <p className="text-xs text-slate-600 line-clamp-2">{c.consultation_notes}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create / Edit Modal Dialog */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Pill className="h-5 w-5 text-teal-600" />
              <span>{modalMode === 'create' ? 'Write Prescription' : 'Edit Prescription'}</span>
            </DialogTitle>
            <DialogDescription>
              Add medications and notes for{' '}
              <span className="font-semibold text-slate-800">
                {selectedConsultationId && consultationMap.get(selectedConsultationId)?.patient_name}
              </span>
              .
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-6 py-2">
            {/* Medications List */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-800">Medications</h3>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addMedicationRow}
                  className="h-8 text-xs border-slate-200 hover:bg-slate-50 flex items-center gap-1"
                >
                  <Plus className="h-3.5 w-3.5 text-slate-500" />
                  Add Medication
                </Button>
              </div>

              <div className="space-y-3">
                {medications.map((med, index) => (
                  <div
                    key={index}
                    className="p-3 bg-slate-50 rounded-lg border border-slate-200 relative group space-y-3"
                  >
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                          Drug Name *
                        </label>
                        <Input
                          placeholder="e.g. Paracetamol"
                          value={med.drug_name}
                          onChange={(e) => handleMedicationChange(index, 'drug_name', e.target.value)}
                          className="bg-white border-slate-200 text-sm h-9"
                          required
                        />
                      </div>
                      <div>
                        <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                          Dosage *
                        </label>
                        <Input
                          placeholder="e.g. 500mg, 1 tablet"
                          value={med.dosage}
                          onChange={(e) => handleMedicationChange(index, 'dosage', e.target.value)}
                          className="bg-white border-slate-200 text-sm h-9"
                          required
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                          Frequency *
                        </label>
                        <Input
                          placeholder="e.g. Twice daily"
                          value={med.frequency}
                          onChange={(e) => handleMedicationChange(index, 'frequency', e.target.value)}
                          className="bg-white border-slate-200 text-sm h-9"
                          required
                        />
                      </div>
                      <div>
                        <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                          Duration *
                        </label>
                        <Input
                          placeholder="e.g. 5 days, 1 week"
                          value={med.duration}
                          onChange={(e) => handleMedicationChange(index, 'duration', e.target.value)}
                          className="bg-white border-slate-200 text-sm h-9"
                          required
                        />
                      </div>
                      <div>
                        <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                          Instructions (Optional)
                        </label>
                        <Input
                          placeholder="e.g. Take after food"
                          value={med.instructions}
                          onChange={(e) => handleMedicationChange(index, 'instructions', e.target.value)}
                          className="bg-white border-slate-200 text-sm h-9"
                        />
                      </div>
                    </div>

                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removeMedicationRow(index)}
                      className="absolute right-2 top-2 h-7 w-7 text-red-500 hover:text-red-600 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            {/* Additional dosage instructions */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700 block">
                Additional Dosage Instructions (Optional)
              </label>
              <Textarea
                placeholder="Specify general dietary instructions, warnings, or guidelines..."
                value={dosageInstructions}
                onChange={(e) => setDosageInstructions(e.target.value)}
                className="min-h-16 border-slate-200 text-sm"
              />
            </div>

            {/* General notes */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700 block">
                General Notes (Optional)
              </label>
              <Textarea
                placeholder="Any general comments about this prescription..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="min-h-16 border-slate-200 text-sm"
              />
            </div>

            {/* Footer buttons */}
            <DialogFooter className="gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsModalOpen(false)}
                className="border-slate-300 hover:bg-slate-50 text-slate-700 text-sm h-10"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createPrescriptionMutation.isPending || updatePrescriptionMutation.isPending}
                className="bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm h-10 px-6 flex items-center justify-center gap-1.5"
              >
                {modalMode === 'create' ? 'Create & Issue' : 'Save Changes'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
