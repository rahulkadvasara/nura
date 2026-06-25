import { useQuery } from '@tanstack/react-query'
import { doctorEarningsService } from '@/services/doctor-earnings.service'
import {
  DoctorEarningsResponse,
  DoctorWalletDetailsResponse,
  DoctorTransactionsResponse,
} from '@/types'

export function useDoctorEarnings(params?: {
  start_date?: string
  end_date?: string
  limit?: number
  skip?: number
  sort_by?: string
}) {
  return useQuery<DoctorEarningsResponse>({
    queryKey: ['doctor', 'earnings', params],
    queryFn: async () => {
      const response = await doctorEarningsService.getEarnings(params)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch doctor earnings')
    },
    placeholderData: (previousData) => previousData,
  })
}

export function useDoctorWallet() {
  return useQuery<DoctorWalletDetailsResponse>({
    queryKey: ['doctor', 'wallet'],
    queryFn: async () => {
      const response = await doctorEarningsService.getWallet()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch doctor wallet details')
    },
  })
}

export function useDoctorTransactions(params?: {
  start_date?: string
  end_date?: string
  status?: string
  limit?: number
  skip?: number
}) {
  return useQuery<DoctorTransactionsResponse>({
    queryKey: ['doctor', 'transactions', params],
    queryFn: async () => {
      const response = await doctorEarningsService.getTransactions(params)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch doctor transactions')
    },
    placeholderData: (previousData) => previousData,
  })
}
