import botService from '@/services/api/botService';
import api from '@/services/api/index';

// Mock the api module
jest.mock('@/services/api/index');

describe('botService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getT1BuyFX', () => {
    it('should call GET /bot/t1-buy-fx with date parameter', async () => {
      const mockResponse = {
        data: {
          success: true,
          data: {
            items: [
              {
                transaction_no: 'TXN001',
                customer_id: '1234567890123',
                currency: 'USD',
                foreign_amount: 1000,
                local_amount: 35000
              }
            ],
            total: 1,
            total_amount_thb: 35000
          }
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const date = '2025-01-15';
      const result = await botService.getT1BuyFX(date);

      expect(api.get).toHaveBeenCalledWith('/bot/t1-buy-fx', {
        params: { date }
      });
      expect(result).toEqual(mockResponse);
    });

    it('should work without date parameter', async () => {
      const mockResponse = { data: { success: true, data: { items: [], total: 0 } } };
      api.get.mockResolvedValue(mockResponse);

      await botService.getT1BuyFX();

      expect(api.get).toHaveBeenCalledWith('/bot/t1-buy-fx', {
        params: { date: undefined }
      });
    });
  });

  describe('getT1SellFX', () => {
    it('should call GET /bot/t1-sell-fx with date parameter', async () => {
      const mockResponse = {
        data: {
          success: true,
          data: {
            items: [
              {
                transaction_no: 'TXN002',
                customer_id: '9876543210987',
                currency: 'EUR',
                foreign_amount: 500,
                local_amount: 19000
              }
            ],
            total: 1,
            total_amount_thb: 19000
          }
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const date = '2025-01-15';
      const result = await botService.getT1SellFX(date);

      expect(api.get).toHaveBeenCalledWith('/bot/t1-sell-fx', {
        params: { date }
      });
      expect(result).toEqual(mockResponse);
    });

    it('should work without date parameter', async () => {
      const mockResponse = { data: { success: true, data: { items: [], total: 0 } } };
      api.get.mockResolvedValue(mockResponse);

      await botService.getT1SellFX();

      expect(api.get).toHaveBeenCalledWith('/bot/t1-sell-fx', {
        params: { date: undefined }
      });
    });
  });

  describe('exportBuyFX', () => {
    it('should call GET /bot/export-buy-fx with blob responseType', async () => {
      const mockBlob = new Blob(['Excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const mockResponse = {
        data: mockBlob
      };

      api.get.mockResolvedValue(mockResponse);

      const date = '2025-01-15';
      const result = await botService.exportBuyFX(date);

      expect(api.get).toHaveBeenCalledWith('/bot/export-buy-fx', {
        params: { date },
        responseType: 'blob'
      });
      expect(result).toEqual(mockResponse);
      expect(result.data).toBeInstanceOf(Blob);
    });

    it('should handle export error', async () => {
      const error = new Error('Export failed');
      api.get.mockRejectedValue(error);

      await expect(botService.exportBuyFX('2025-01-15')).rejects.toThrow('Export failed');
    });
  });

  describe('exportSellFX', () => {
    it('should call GET /bot/export-sell-fx with blob responseType', async () => {
      const mockBlob = new Blob(['Excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const mockResponse = {
        data: mockBlob
      };

      api.get.mockResolvedValue(mockResponse);

      const date = '2025-01-15';
      const result = await botService.exportSellFX(date);

      expect(api.get).toHaveBeenCalledWith('/bot/export-sell-fx', {
        params: { date },
        responseType: 'blob'
      });
      expect(result).toEqual(mockResponse);
      expect(result.data).toBeInstanceOf(Blob);
    });

    it('should handle export error', async () => {
      const error = new Error('Export failed');
      api.get.mockRejectedValue(error);

      await expect(botService.exportSellFX('2025-01-15')).rejects.toThrow('Export failed');
    });
  });

  describe('saveBuyFX', () => {
    it('should call POST /bot/save-buy-fx with data', async () => {
      const mockResponse = {
        data: {
          success: true,
          message: 'Buy FX report saved'
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const data = {
        transaction_id: 123,
        report_date: '2025-01-15',
        json_data: {
          currency: 'USD',
          amount: 1000
        }
      };

      const result = await botService.saveBuyFX(data);

      expect(api.post).toHaveBeenCalledWith('/bot/save-buy-fx', data);
      expect(result).toEqual(mockResponse);
    });

    it('should handle save error', async () => {
      const error = new Error('Save failed');
      api.post.mockRejectedValue(error);

      const data = {
        transaction_id: 123,
        report_date: '2025-01-15',
        json_data: {}
      };

      await expect(botService.saveBuyFX(data)).rejects.toThrow('Save failed');
    });
  });

  describe('saveSellFX', () => {
    it('should call POST /bot/save-sell-fx with data', async () => {
      const mockResponse = {
        data: {
          success: true,
          message: 'Sell FX report saved'
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const data = {
        transaction_id: 456,
        report_date: '2025-01-15',
        json_data: {
          currency: 'EUR',
          amount: 500
        }
      };

      const result = await botService.saveSellFX(data);

      expect(api.post).toHaveBeenCalledWith('/bot/save-sell-fx', data);
      expect(result).toEqual(mockResponse);
    });

    it('should handle save error', async () => {
      const error = new Error('Save failed');
      api.post.mockRejectedValue(error);

      const data = {
        transaction_id: 456,
        report_date: '2025-01-15',
        json_data: {}
      };

      await expect(botService.saveSellFX(data)).rejects.toThrow('Save failed');
    });
  });

  describe('exportMultiSheetExcel', () => {
    it('should call both exportBuyFX and exportSellFX in parallel', async () => {
      const mockBuyBlob = new Blob(['Buy Excel'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const mockSellBlob = new Blob(['Sell Excel'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });

      const mockBuyResponse = { data: mockBuyBlob };
      const mockSellResponse = { data: mockSellBlob };

      api.get.mockImplementation((url) => {
        if (url === '/bot/export-buy-fx') {
          return Promise.resolve(mockBuyResponse);
        } else if (url === '/bot/export-sell-fx') {
          return Promise.resolve(mockSellResponse);
        }
      });

      const date = '2025-01-15';
      const result = await botService.exportMultiSheetExcel(date);

      expect(api.get).toHaveBeenCalledTimes(2);
      expect(api.get).toHaveBeenCalledWith('/bot/export-buy-fx', {
        params: { date },
        responseType: 'blob'
      });
      expect(api.get).toHaveBeenCalledWith('/bot/export-sell-fx', {
        params: { date },
        responseType: 'blob'
      });

      expect(result).toEqual({
        buyData: mockBuyResponse,
        sellData: mockSellResponse
      });
    });

    it('should handle partial failure in multi-sheet export', async () => {
      const mockBuyBlob = new Blob(['Buy Excel'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });

      api.get.mockImplementation((url) => {
        if (url === '/bot/export-buy-fx') {
          return Promise.resolve({ data: mockBuyBlob });
        } else if (url === '/bot/export-sell-fx') {
          return Promise.reject(new Error('Sell export failed'));
        }
      });

      const date = '2025-01-15';

      await expect(botService.exportMultiSheetExcel(date)).rejects.toThrow('Sell export failed');
    });
  });

  describe('getTriggerConfig', () => {
    it('should call GET /bot/trigger-config', async () => {
      const mockResponse = {
        data: {
          success: true,
          data: {
            buy_threshold: 450000,
            sell_threshold: 450000,
            enabled: true
          }
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const result = await botService.getTriggerConfig();

      expect(api.get).toHaveBeenCalledWith('/bot/trigger-config');
      expect(result).toEqual(mockResponse);
    });

    it('should handle get config error', async () => {
      const error = new Error('Config not found');
      api.get.mockRejectedValue(error);

      await expect(botService.getTriggerConfig()).rejects.toThrow('Config not found');
    });
  });

  describe('saveTriggerConfig', () => {
    it('should call POST /bot/trigger-config with config data', async () => {
      const mockResponse = {
        data: {
          success: true,
          message: 'Config saved'
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const config = {
        buy_threshold: 500000,
        sell_threshold: 500000,
        enabled: true
      };

      const result = await botService.saveTriggerConfig(config);

      expect(api.post).toHaveBeenCalledWith('/bot/trigger-config', config);
      expect(result).toEqual(mockResponse);
    });

    it('should handle save config error', async () => {
      const error = new Error('Save config failed');
      api.post.mockRejectedValue(error);

      const config = {
        buy_threshold: 500000,
        sell_threshold: 500000,
        enabled: true
      };

      await expect(botService.saveTriggerConfig(config)).rejects.toThrow('Save config failed');
    });

    it('should save config with disabled state', async () => {
      const mockResponse = { data: { success: true } };
      api.post.mockResolvedValue(mockResponse);

      const config = {
        buy_threshold: 0,
        sell_threshold: 0,
        enabled: false
      };

      await botService.saveTriggerConfig(config);

      expect(api.post).toHaveBeenCalledWith('/bot/trigger-config', {
        buy_threshold: 0,
        sell_threshold: 0,
        enabled: false
      });
    });
  });

  describe('Date Parameter Handling', () => {
    it('should handle various date formats', async () => {
      const mockResponse = { data: { success: true, data: { items: [], total: 0 } } };
      api.get.mockResolvedValue(mockResponse);

      // ISO format
      await botService.getT1BuyFX('2025-01-15');
      expect(api.get).toHaveBeenCalledWith('/bot/t1-buy-fx', {
        params: { date: '2025-01-15' }
      });

      // Different date
      await botService.getT1SellFX('2024-12-31');
      expect(api.get).toHaveBeenCalledWith('/bot/t1-sell-fx', {
        params: { date: '2024-12-31' }
      });
    });

    it('should handle empty date string', async () => {
      const mockResponse = { data: { success: true, data: { items: [], total: 0 } } };
      api.get.mockResolvedValue(mockResponse);

      await botService.getT1BuyFX('');

      expect(api.get).toHaveBeenCalledWith('/bot/t1-buy-fx', {
        params: { date: '' }
      });
    });
  });

  describe('Error Handling', () => {
    it('should propagate network errors', async () => {
      const error = new Error('Network error');
      api.get.mockRejectedValue(error);

      await expect(botService.getT1BuyFX('2025-01-15')).rejects.toThrow('Network error');
    });

    it('should handle 401 unauthorized errors', async () => {
      const error = {
        response: {
          status: 401,
          data: { message: 'Unauthorized' }
        }
      };
      api.get.mockRejectedValue(error);

      await expect(botService.exportBuyFX('2025-01-15')).rejects.toEqual(error);
    });

    it('should handle 500 server errors', async () => {
      const error = {
        response: {
          status: 500,
          data: { message: 'Internal server error' }
        }
      };
      api.post.mockRejectedValue(error);

      const data = {
        transaction_id: 123,
        report_date: '2025-01-15',
        json_data: {}
      };

      await expect(botService.saveBuyFX(data)).rejects.toEqual(error);
    });
  });

  describe('Blob Response Handling', () => {
    it('should correctly handle Excel blob responses', async () => {
      const excelContent = 'Mock Excel Binary Content';
      const mockBlob = new Blob([excelContent], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });

      api.get.mockResolvedValue({ data: mockBlob });

      const result = await botService.exportBuyFX('2025-01-15');

      expect(result.data).toBeInstanceOf(Blob);
      expect(result.data.type).toBe('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    });

    it('should preserve blob size', async () => {
      const largeContent = 'A'.repeat(10000);
      const mockBlob = new Blob([largeContent], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });

      api.get.mockResolvedValue({ data: mockBlob });

      const result = await botService.exportSellFX('2025-01-15');

      expect(result.data.size).toBe(10000);
    });
  });
});
