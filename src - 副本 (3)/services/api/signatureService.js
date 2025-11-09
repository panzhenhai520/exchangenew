/**
 * Signature API Service
 *
 * Provides API methods for managing AMLO reservation signatures:
 * - Save reporter/customer/auditor signatures
 * - Retrieve signatures
 * - Delete individual signatures
 *
 * All signatures are stored as Base64-encoded PNG images.
 */

import apiClient from './apiClient'

const signatureService = {
  /**
   * Save signatures for a reservation
   *
   * @param {number} reservationId - Reservation ID
   * @param {Object} signatures - Signature data
   * @param {string} [signatures.reporter_signature] - Reporter's signature (Base64 PNG)
   * @param {string} [signatures.customer_signature] - Customer's signature (Base64 PNG)
   * @param {string} [signatures.auditor_signature] - Auditor's signature (Base64 PNG)
   * @param {string} [signatures.storage_type='base64'] - Storage type: 'base64' or 'file'
   * @returns {Promise} Response with saved signatures info
   */
  async saveSignatures(reservationId, signatures) {
    try {
      const response = await apiClient.post(`/api/amlo/reservations/${reservationId}/signatures`, signatures)
      return response.data
    } catch (error) {
      console.error('[signatureService] Save signatures error:', error)
      throw error
    }
  },

  /**
   * Get all signatures for a reservation
   *
   * @param {number} reservationId - Reservation ID
   * @returns {Promise} Signature data including all three signatures and timestamps
   */
  async getSignatures(reservationId) {
    try {
      const response = await apiClient.get(`/api/amlo/reservations/${reservationId}/signatures`)
      return response.data
    } catch (error) {
      console.error('[signatureService] Get signatures error:', error)
      throw error
    }
  },

  /**
   * Delete a specific signature
   *
   * @param {number} reservationId - Reservation ID
   * @param {string} signatureType - Type: 'reporter', 'customer', or 'auditor'
   * @returns {Promise} Delete confirmation
   */
  async deleteSignature(reservationId, signatureType) {
    try {
      const response = await apiClient.delete(`/api/amlo/reservations/${reservationId}/signatures/${signatureType}`)
      return response.data
    } catch (error) {
      console.error('[signatureService] Delete signature error:', error)
      throw error
    }
  },

  /**
   * Check if a reservation has signatures
   *
   * @param {number} reservationId - Reservation ID
   * @returns {Promise<Object>} Object with boolean flags: {hasReporter, hasCustomer, hasAuditor}
   */
  async hasSignatures(reservationId) {
    try {
      const response = await this.getSignatures(reservationId)
      if (response.success && response.data) {
        return {
          hasReporter: !!response.data.reporter_signature,
          hasCustomer: !!response.data.customer_signature,
          hasAuditor: !!response.data.auditor_signature
        }
      }
      return { hasReporter: false, hasCustomer: false, hasAuditor: false }
    } catch (error) {
      console.error('[signatureService] Check signatures error:', error)
      return { hasReporter: false, hasCustomer: false, hasAuditor: false }
    }
  },

  /**
   * Validate signature data before saving
   *
   * @param {string} signatureData - Base64 PNG signature data
   * @returns {Object} Validation result: {valid: boolean, error: string|null, size: number}
   */
  validateSignatureData(signatureData) {
    const MAX_SIZE = 500 * 1024 // 500KB

    if (!signatureData) {
      return { valid: false, error: 'Signature data is empty', size: 0 }
    }

    if (!signatureData.startsWith('data:image/png;base64,')) {
      return { valid: false, error: 'Invalid format: must be data:image/png;base64,...', size: signatureData.length }
    }

    if (signatureData.length > MAX_SIZE) {
      return {
        valid: false,
        error: `Signature too large: ${(signatureData.length / 1024).toFixed(2)}KB (max 500KB)`,
        size: signatureData.length
      }
    }

    return { valid: true, error: null, size: signatureData.length }
  }
}

export default signatureService
