import apiClient from '@/lib/axios'
import { ApiResponse, AdminAnalyticsData } from '@/types'

export const adminAnalyticsService = {
  getAnalytics: async (): Promise<ApiResponse<AdminAnalyticsData>> => {
    const response = await apiClient.get<ApiResponse<AdminAnalyticsData>>('/admin/analytics')
    return response.data
  }
}
