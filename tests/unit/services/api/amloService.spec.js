import amloService from '@/services/api/amloService';
import api from '@/services/api/index';

// Mock the api module
jest.mock('@/services/api/index');

describe('amloService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getReservations', () => {
    it('should call GET /amlo/reservations with params', async () => {
      const mockResponse = {
        data: {
          success: true,
          data: {
            items: [],
            total: 0
          }
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const params = {
        status: 'pending',
        page: 1,
        page_size: 20
      };

      const result = await amloService.getReservations(params);

      expect(api.get).toHaveBeenCalledWith('/amlo/reservations', { params });
      expect(result).toEqual(mockResponse);
    });

    it('should work with empty params', async () => {
      const mockResponse = { data: { success: true } };
      api.get.mockResolvedValue(mockResponse);

      await amloService.getReservations();

      expect(api.get).toHaveBeenCalledWith('/amlo/reservations', { params: {} });
    });
  });

  describe('auditReservation', () => {
    it('should call POST /amlo/reservations/{id}/audit with data', async () => {
      const mockResponse = {
        data: {
          success: true,
          message: 'Audit successful'
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const reservationId = 123;
      const data = {
        action: 'approve',
        remarks: 'Test approval'
      };

      const result = await amloService.auditReservation(reservationId, data);

      expect(api.post).toHaveBeenCalledWith('/amlo/reservations/123/audit', data);
      expect(result).toEqual(mockResponse);
    });

    it('should handle rejection with reason', async () => {
      const mockResponse = { data: { success: true } };
      api.post.mockResolvedValue(mockResponse);

      const data = {
        action: 'reject',
        rejection_reason: 'Invalid documents',
        remarks: 'Please resubmit'
      };

      await amloService.auditReservation(456, data);

      expect(api.post).toHaveBeenCalledWith('/amlo/reservations/456/audit', data);
    });
  });

  describe('reverseAudit', () => {
    it('should call POST /amlo/reservations/{id}/reverse-audit', async () => {
      const mockResponse = { data: { success: true } };
      api.post.mockResolvedValue(mockResponse);

      const data = { remarks: 'Reversing audit' };
      await amloService.reverseAudit(789, data);

      expect(api.post).toHaveBeenCalledWith('/amlo/reservations/789/reverse-audit', data);
    });

    it('should work with empty data object', async () => {
      const mockResponse = { data: { success: true } };
      api.post.mockResolvedValue(mockResponse);

      await amloService.reverseAudit(123);

      expect(api.post).toHaveBeenCalledWith('/amlo/reservations/123/reverse-audit', {});
    });
  });

  describe('getReports', () => {
    it('should call GET /amlo/reports with params', async () => {
      const mockResponse = {
        data: {
          success: true,
          data: {
            items: [
              {
                id: 1,
                report_type: 'AMLO-1-01',
                is_reported: false
              }
            ],
            total: 1
          }
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const params = {
        is_reported: false,
        report_type: 'AMLO-1-01',
        page: 1,
        page_size: 20
      };

      const result = await amloService.getReports(params);

      expect(api.get).toHaveBeenCalledWith('/amlo/reports', { params });
      expect(result).toEqual(mockResponse);
    });

    it('should handle status filter correctly', async () => {
      const mockResponse = { data: { success: true, data: { items: [], total: 0 } } };
      api.get.mockResolvedValue(mockResponse);

      const params = {
        status: 'pending',
        start_date: '2025-01-01',
        end_date: '2025-12-31'
      };

      await amloService.getReports(params);

      expect(api.get).toHaveBeenCalledWith('/amlo/reports', { params });
    });
  });

  describe('batchReport', () => {
    it('should call POST /amlo/reports/batch-report with report IDs', async () => {
      const mockResponse = {
        data: {
          success: true,
          message: 'Batch report successful'
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const reportIds = [1, 2, 3];
      const result = await amloService.batchReport(reportIds);

      expect(api.post).toHaveBeenCalledWith('/amlo/reports/batch-report', {
        report_ids: reportIds
      });
      expect(result).toEqual(mockResponse);
    });

    it('should handle single report ID', async () => {
      const mockResponse = { data: { success: true } };
      api.post.mockResolvedValue(mockResponse);

      await amloService.batchReport([456]);

      expect(api.post).toHaveBeenCalledWith('/amlo/reports/batch-report', {
        report_ids: [456]
      });
    });

    it('should handle empty array', async () => {
      const mockResponse = { data: { success: false } };
      api.post.mockResolvedValue(mockResponse);

      await amloService.batchReport([]);

      expect(api.post).toHaveBeenCalledWith('/amlo/reports/batch-report', {
        report_ids: []
      });
    });
  });

  describe('completeReservation', () => {
    it('should call POST /amlo/reservations/{id}/complete with linked transaction', async () => {
      const mockResponse = {
        data: {
          success: true,
          message: 'Reservation completed'
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const reservationId = 123;
      const data = {
        linked_transaction_id: 456
      };

      const result = await amloService.completeReservation(reservationId, data);

      expect(api.post).toHaveBeenCalledWith('/amlo/reservations/123/complete', data);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('generateReportPDF', () => {
    it('should call GET /amlo/reports/{id}/generate-pdf with blob responseType', async () => {
      const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' });
      const mockResponse = {
        data: mockBlob
      };

      api.get.mockResolvedValue(mockResponse);

      const reportId = 789;
      const result = await amloService.generateReportPDF(reportId);

      expect(api.get).toHaveBeenCalledWith('/amlo/reports/789/generate-pdf', {
        responseType: 'blob'
      });
      expect(result).toEqual(mockResponse);
      expect(result.data).toBeInstanceOf(Blob);
    });

    it('should handle PDF generation error', async () => {
      const error = new Error('PDF generation failed');
      api.get.mockRejectedValue(error);

      await expect(amloService.generateReportPDF(123)).rejects.toThrow('PDF generation failed');
    });
  });

  describe('batchGeneratePDF', () => {
    it('should call POST /amlo/reports/batch-generate-pdf with report IDs and blob responseType', async () => {
      const mockBlob = new Blob(['ZIP content'], { type: 'application/zip' });
      const mockResponse = {
        data: mockBlob
      };

      api.post.mockResolvedValue(mockResponse);

      const reportIds = [1, 2, 3];
      const result = await amloService.batchGeneratePDF(reportIds);

      expect(api.post).toHaveBeenCalledWith(
        '/amlo/reports/batch-generate-pdf',
        {
          report_ids: reportIds
        },
        {
          responseType: 'blob'
        }
      );
      expect(result).toEqual(mockResponse);
      expect(result.data).toBeInstanceOf(Blob);
    });

    it('should handle single report ID in batch PDF', async () => {
      const mockBlob = new Blob(['ZIP content'], { type: 'application/zip' });
      api.post.mockResolvedValue({ data: mockBlob });

      await amloService.batchGeneratePDF([456]);

      expect(api.post).toHaveBeenCalledWith(
        '/amlo/reports/batch-generate-pdf',
        { report_ids: [456] },
        { responseType: 'blob' }
      );
    });

    it('should handle batch PDF generation error', async () => {
      const error = new Error('Batch PDF generation failed');
      api.post.mockRejectedValue(error);

      await expect(amloService.batchGeneratePDF([1, 2])).rejects.toThrow('Batch PDF generation failed');
    });
  });

  describe('Error Handling', () => {
    it('should propagate API errors', async () => {
      const error = new Error('Network error');
      api.get.mockRejectedValue(error);

      await expect(amloService.getReservations()).rejects.toThrow('Network error');
    });

    it('should handle 404 errors', async () => {
      const error = {
        response: {
          status: 404,
          data: { message: 'Not found' }
        }
      };
      api.get.mockRejectedValue(error);

      await expect(amloService.generateReportPDF(999)).rejects.toEqual(error);
    });

    it('should handle 500 errors', async () => {
      const error = {
        response: {
          status: 500,
          data: { message: 'Internal server error' }
        }
      };
      api.post.mockRejectedValue(error);

      await expect(amloService.batchReport([1, 2])).rejects.toEqual(error);
    });
  });

  describe('Parameter Validation', () => {
    it('should pass all filter parameters correctly', async () => {
      const mockResponse = { data: { success: true, data: { items: [], total: 0 } } };
      api.get.mockResolvedValue(mockResponse);

      const params = {
        status: 'pending',
        report_type: 'AMLO-1-02',
        start_date: '2025-01-01',
        end_date: '2025-12-31',
        customer_id: '1234567890123',
        page: 2,
        page_size: 50
      };

      await amloService.getReports(params);

      expect(api.get).toHaveBeenCalledWith('/amlo/reports', {
        params: expect.objectContaining({
          status: 'pending',
          report_type: 'AMLO-1-02',
          start_date: '2025-01-01',
          end_date: '2025-12-31',
          customer_id: '1234567890123',
          page: 2,
          page_size: 50
        })
      });
    });

    it('should handle numeric IDs correctly', async () => {
      const mockResponse = { data: { success: true } };
      api.get.mockResolvedValue(mockResponse);

      await amloService.generateReportPDF(123);
      expect(api.get).toHaveBeenCalledWith('/amlo/reports/123/generate-pdf', { responseType: 'blob' });

      await amloService.generateReportPDF(0);
      expect(api.get).toHaveBeenCalledWith('/amlo/reports/0/generate-pdf', { responseType: 'blob' });
    });
  });
});
