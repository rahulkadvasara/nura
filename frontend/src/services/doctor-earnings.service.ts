import apiClient from '@/lib/axios'
import {
  ApiResponse,
  DoctorEarningsResponse,
  DoctorWalletDetailsResponse,
  DoctorTransactionsResponse,
} from '@/types'

export const doctorEarningsService = {
  getEarnings: async (params?: {
    start_date?: string
    end_date?: string
    limit?: number
    skip?: number
    sort_by?: string
  }): Promise<ApiResponse<DoctorEarningsResponse>> => {
    const response = await apiClient.get<ApiResponse<DoctorEarningsResponse>>('/doctor/earnings', { params })
    return response.data
  },

  getWallet: async (): Promise<ApiResponse<DoctorWalletDetailsResponse>> => {
    const response = await apiClient.get<ApiResponse<DoctorWalletDetailsResponse>>('/doctor/wallet')
    return response.data
  },

  getTransactions: async (params?: {
    start_date?: string
    end_date?: string
    status?: string
    limit?: number
    skip?: number
  }): Promise<ApiResponse<DoctorTransactionsResponse>> => {
    // Map status from react parameters to backend status_filter parameter
    const queryParams: Record<string, any> = {
      start_date: params?.start_date,
      end_date: params?.end_date,
      status_filter: params?.status,
      limit: params?.limit,
      skip: params?.skip,
    }
    const response = await apiClient.get<ApiResponse<DoctorTransactionsResponse>>('/doctor/transactions', {
      params: queryParams,
    })
    return response.data
  },
}
