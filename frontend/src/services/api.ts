/**
 * ORCA API Service
 * Handles all backend communication
 */

import axios, { AxiosInstance } from 'axios';
import { ReasonResponse } from '@/types';

class OrcaApiService {
  private api: AxiosInstance;

  constructor(baseURL: string = '/api') {
    this.api = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Health check endpoint
   */
  async health(): Promise<{ status: string }> {
    try {
      const response = await this.api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  /**
   * Main reasoning endpoint
   * Sends a natural language query and returns structured recommendation
   */
  async reason(query: string): Promise<ReasonResponse> {
    try {
      const response = await this.api.post<ReasonResponse>('/v1/reason', {
        query,
      });
      return response.data;
    } catch (error) {
      console.error('Reason request failed:', error);
      throw error;
    }
  }
}

export default new OrcaApiService(
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
);
