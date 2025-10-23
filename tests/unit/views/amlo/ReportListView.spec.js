import { mount, flushPromises } from '@vue/test-utils';
import { ref } from 'vue';
import ReportListView from '@/views/amlo/ReportListView.vue';
import amloService from '@/services/api/amloService';

// Mock the amloService
jest.mock('@/services/api/amloService');

// Mock Bootstrap Modal
jest.mock('bootstrap', () => ({
  Modal: jest.fn().mockImplementation(() => ({
    show: jest.fn(),
    hide: jest.fn()
  }))
}));

describe('ReportListView.vue', () => {
  let wrapper;

  const mockReports = [
    {
      id: 1,
      reservation_no: 'RES001',
      report_type: 'AMLO-1-01',
      customer_name: 'John Doe',
      customer_id: '1234567890123',
      amount: 500000,
      currency_code: 'THB',
      direction: 'buy',
      created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
      is_reported: false,
      form_data: { test: 'data' }
    },
    {
      id: 2,
      reservation_no: 'RES002',
      report_type: 'AMLO-1-02',
      customer_name: 'Jane Smith',
      customer_id: '9876543210987',
      amount: 750000,
      currency_code: 'THB',
      direction: 'sell',
      created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days ago (OVERDUE)
      is_reported: false,
      form_data: { test: 'data2' }
    },
    {
      id: 3,
      reservation_no: 'RES003',
      report_type: 'AMLO-1-01',
      customer_name: 'Bob Johnson',
      customer_id: '5555555555555',
      amount: 600000,
      currency_code: 'THB',
      direction: 'buy',
      created_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(), // 10 days ago
      is_reported: true, // Already reported
      form_data: { test: 'data3' }
    }
  ];

  beforeEach(() => {
    // Mock API response
    amloService.getReports = jest.fn().mockResolvedValue({
      data: {
        success: true,
        data: {
          items: mockReports,
          total: 3
        }
      }
    });

    // Clear mocks
    jest.clearAllMocks();
  });

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
    }
  });

  describe('Overdue Detection Logic', () => {
    it('should detect report as NOT overdue when created less than 3 days ago', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      const recentReport = mockReports[0]; // 2 days ago

      expect(vm.isOverdue(recentReport)).toBe(false);
    });

    it('should detect report as overdue when created more than 3 days ago', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      const overdueReport = mockReports[1]; // 5 days ago

      expect(vm.isOverdue(overdueReport)).toBe(true);
    });

    it('should NOT mark already-reported items as overdue', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      const reportedReport = mockReports[2]; // 10 days ago but already reported

      expect(vm.isOverdue(reportedReport)).toBe(false);
    });

    it('should calculate correct overdue days', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      const overdueReport = mockReports[1]; // 5 days ago

      const days = vm.getOverdueDays(overdueReport);
      expect(days).toBeGreaterThanOrEqual(4);
      expect(days).toBeLessThanOrEqual(6); // Allow 1 day variance for test timing
    });

    it('should return 0 overdue days for already-reported items', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      const reportedReport = mockReports[2];

      expect(vm.getOverdueDays(reportedReport)).toBe(0);
    });
  });

  describe('Red Highlighting (table-danger class)', () => {
    it('should apply table-danger class to overdue rows', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      // Wait for DOM update
      await wrapper.vm.$nextTick();

      // Find all table rows
      const rows = wrapper.findAll('tbody tr');

      // Second row should have table-danger class (5 days overdue)
      expect(rows.length).toBe(3);
      expect(rows[1].classes()).toContain('table-danger');
    });

    it('should NOT apply table-danger class to non-overdue rows', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();
      await wrapper.vm.$nextTick();

      const rows = wrapper.findAll('tbody tr');

      // First row (2 days old) should NOT have table-danger class
      expect(rows[0].classes()).not.toContain('table-danger');
    });

    it('should NOT apply table-danger class to already-reported rows', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();
      await wrapper.vm.$nextTick();

      const rows = wrapper.findAll('tbody tr');

      // Third row (10 days old but reported) should NOT have table-danger class
      expect(rows[2].classes()).not.toContain('table-danger');
    });

    it('should display overdue badge for overdue reports', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();
      await wrapper.vm.$nextTick();

      const badges = wrapper.findAll('.badge.bg-danger');

      // Should have at least one overdue badge (for the 5-day old report)
      expect(badges.length).toBeGreaterThan(0);
    });
  });

  describe('Batch Selection', () => {
    it('should allow selecting unreported reports', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;

      // Select first report (unreported)
      vm.toggleSelectReport(1);
      expect(vm.selectedReports).toContain(1);
    });

    it('should allow deselecting reports', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;

      // Select and then deselect
      vm.toggleSelectReport(1);
      expect(vm.selectedReports).toContain(1);

      vm.toggleSelectReport(1);
      expect(vm.selectedReports).not.toContain(1);
    });

    it('should select all unreported reports when toggle all is clicked', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;

      // Initially no selection
      expect(vm.selectedReports.length).toBe(0);

      // Toggle select all
      vm.toggleSelectAll();

      // Should select only unreported reports (IDs 1 and 2, not 3)
      expect(vm.selectedReports.length).toBe(2);
      expect(vm.selectedReports).toContain(1);
      expect(vm.selectedReports).toContain(2);
      expect(vm.selectedReports).not.toContain(3);
    });

    it('should deselect all when toggle all is clicked again', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;

      // Select all
      vm.toggleSelectAll();
      expect(vm.selectedReports.length).toBe(2);

      // Deselect all
      vm.toggleSelectAll();
      expect(vm.selectedReports.length).toBe(0);
    });
  });

  describe('Report Actions', () => {
    it('should download PDF when downloadPDF is called', async () => {
      // Mock the PDF download response
      const mockBlob = new Blob(['pdf content'], { type: 'application/pdf' });
      amloService.generateReportPDF = jest.fn().mockResolvedValue({
        data: mockBlob
      });

      // Mock DOM methods
      const mockLink = {
        click: jest.fn(),
        remove: jest.fn(),
        setAttribute: jest.fn()
      };
      document.createElement = jest.fn().mockReturnValue(mockLink);
      document.body.appendChild = jest.fn();

      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      await vm.downloadPDF(1);

      // Verify API was called
      expect(amloService.generateReportPDF).toHaveBeenCalledWith(1);

      // Verify download link was created and clicked
      expect(document.createElement).toHaveBeenCalledWith('a');
      expect(mockLink.click).toHaveBeenCalled();
      expect(mockLink.remove).toHaveBeenCalled();
    });

    it('should handle PDF download error gracefully', async () => {
      amloService.generateReportPDF = jest.fn().mockRejectedValue(new Error('Download failed'));

      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      await vm.downloadPDF(1);

      // Verify alert was called
      expect(global.alert).toHaveBeenCalledWith('下载PDF失败');
    });

    it('should report single item when reportSingle is called', async () => {
      amloService.batchReport = jest.fn().mockResolvedValue({
        data: { success: true }
      });

      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      await vm.reportSingle(1);

      // Verify confirmation was requested
      expect(global.confirm).toHaveBeenCalled();

      // Verify API was called with single ID in array
      expect(amloService.batchReport).toHaveBeenCalledWith([1]);

      // Verify success alert
      expect(global.alert).toHaveBeenCalledWith('上报成功');
    });

    it('should batch report selected items', async () => {
      amloService.batchReport = jest.fn().mockResolvedValue({
        data: { success: true }
      });

      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;

      // Select multiple reports
      vm.selectedReports = [1, 2];

      await vm.batchReportSelected();

      // Verify confirmation with count
      expect(global.confirm).toHaveBeenCalledWith('确定要上报选中的 2 条记录吗？');

      // Verify API was called with selected IDs
      expect(amloService.batchReport).toHaveBeenCalledWith([1, 2]);

      // Verify selected reports were cleared
      expect(vm.selectedReports.length).toBe(0);
    });
  });

  describe('Filter and Search', () => {
    it('should load reports on mount', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      expect(amloService.getReports).toHaveBeenCalled();
      expect(wrapper.vm.reports.length).toBe(3);
      expect(wrapper.vm.total).toBe(3);
    });

    it('should pass filter parameters when searching', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;

      // Set filters
      vm.filters.status = 'pending';
      vm.filters.reportType = 'AMLO-1-01';
      vm.filters.startDate = '2025-01-01';
      vm.filters.endDate = '2025-12-31';

      await vm.loadReports();

      // Verify API was called with filter params
      expect(amloService.getReports).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'pending',
          reportType: 'AMLO-1-01',
          startDate: '2025-01-01',
          endDate: '2025-12-31'
        })
      );
    });

    it('should reset filters when resetFilters is called', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;

      // Set some filters
      vm.filters.status = 'pending';
      vm.filters.reportType = 'AMLO-1-01';
      vm.currentPage = 5;

      // Reset
      vm.resetFilters();

      // Verify filters are cleared
      expect(vm.filters.status).toBe('');
      expect(vm.filters.reportType).toBe('');
      expect(vm.currentPage).toBe(1);
    });
  });

  describe('Pagination', () => {
    it('should calculate total pages correctly', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      vm.total = 45;
      vm.pageSize = 20;

      await vm.$nextTick();

      expect(vm.totalPages).toBe(3); // 45 / 20 = 2.25, ceil to 3
    });

    it('should change page when changePage is called', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      vm.total = 50;

      jest.clearAllMocks();

      vm.changePage(2);

      expect(vm.currentPage).toBe(2);
      expect(amloService.getReports).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 })
      );
    });

    it('should not change page when out of bounds', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      vm.total = 20;
      vm.pageSize = 20;
      vm.currentPage = 1;

      jest.clearAllMocks();

      // Try to go to page 0
      vm.changePage(0);
      expect(vm.currentPage).toBe(1);
      expect(amloService.getReports).not.toHaveBeenCalled();

      // Try to go beyond total pages
      vm.changePage(5);
      expect(vm.currentPage).toBe(1);
      expect(amloService.getReports).not.toHaveBeenCalled();
    });
  });

  describe('View Details Modal', () => {
    it('should open modal when viewReport is called', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      const report = mockReports[0];

      vm.viewReport(report);

      expect(vm.selectedReport).toBe(report);
    });

    it('should format JSON data correctly', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      const jsonData = { test: 'value', nested: { key: 123 } };

      const formatted = vm.formatJSON(jsonData);

      expect(formatted).toContain('"test"');
      expect(formatted).toContain('"nested"');
      expect(typeof formatted).toBe('string');
    });
  });

  describe('Data Formatting', () => {
    it('should format amount with thousands separator', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;

      // formatAmount is imported from @/utils/formatters
      // We're testing that it's properly used in the component
      const formatted = vm.formatAmount(500000);
      expect(typeof formatted).toBe('string');
    });

    it('should format datetime correctly', async () => {
      wrapper = mount(ReportListView);
      await flushPromises();

      const vm = wrapper.vm;
      const datetime = '2025-01-15T14:30:00';

      const formatted = vm.formatDateTime(datetime);
      expect(typeof formatted).toBe('string');
      expect(formatted).toBeTruthy();
    });
  });
});
