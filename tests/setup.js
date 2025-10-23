// Global test setup for Jest
import { config } from '@vue/test-utils';

// Mock FontAwesome icons globally
config.global.stubs = {
  'font-awesome-icon': true
};

// Mock i18n globally
config.global.mocks = {
  $t: (key) => key,
  $i18n: {
    locale: 'zh-CN'
  }
};

// Mock window.alert and window.confirm
global.alert = jest.fn();
global.confirm = jest.fn(() => true);

// Mock window.URL.createObjectURL for file downloads
global.URL.createObjectURL = jest.fn(() => 'mock-url');
global.URL.revokeObjectURL = jest.fn();
