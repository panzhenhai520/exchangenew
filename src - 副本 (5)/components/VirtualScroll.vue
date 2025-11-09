<template>
  <div 
    class="virtual-scroll-container"
    :style="{ height: containerHeight + 'px' }"
    @scroll="handleScroll"
    ref="scrollContainer"
  >
    <!-- 总高度占位符 -->
    <div 
      class="virtual-scroll-spacer"
      :style="{ height: totalHeight + 'px' }"
    ></div>
    
    <!-- 可见项目容器 -->
    <div 
      class="virtual-scroll-content"
      :style="{ 
        transform: `translateY(${offsetY}px)`,
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0
      }"
    >
      <div
        v-for="(item, index) in visibleItems"
        :key="getItemKey(item, startIndex + index)"
        class="virtual-scroll-item"
        :style="{ height: itemHeight + 'px' }"
      >
        <slot 
          :item="item" 
          :index="startIndex + index"
          :isVisible="true"
        ></slot>
      </div>
    </div>
    
    <!-- 加载更多指示器 -->
    <div 
      v-if="hasMore && isNearBottom"
      class="virtual-scroll-loading"
      :style="{ 
        position: 'absolute',
        bottom: '10px',
        left: '50%',
        transform: 'translateX(-50%)'
      }"
    >
      <div class="spinner-border spinner-border-sm text-primary" role="status">
        <span class="visually-hidden">加载中...</span>
      </div>
      <span class="ms-2">加载更多...</span>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { VirtualScrollManager, throttle } from '@/utils/performance';

export default {
  name: 'VirtualScroll',
  props: {
    items: {
      type: Array,
      required: true
    },
    itemHeight: {
      type: Number,
      default: 50
    },
    containerHeight: {
      type: Number,
      default: 400
    },
    buffer: {
      type: Number,
      default: 5
    },
    hasMore: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    },
    keyField: {
      type: String,
      default: 'id'
    }
  },
  emits: ['load-more', 'scroll', 'visible-range-change'],
  setup(props, { emit }) {
    const scrollContainer = ref(null);
    const scrollTop = ref(0);
    const isNearBottom = ref(false);
    
    // 虚拟滚动管理器
    const virtualScrollManager = new VirtualScrollManager({
      itemHeight: props.itemHeight,
      containerHeight: props.containerHeight,
      buffer: props.buffer
    });

    // 计算可见范围
    const visibleRange = computed(() => {
      return virtualScrollManager.getVisibleRange(scrollTop.value, props.items.length);
    });

    // 可见项目
    const visibleItems = computed(() => {
      const { startIndex, endIndex } = visibleRange.value;
      return props.items.slice(startIndex, endIndex);
    });

    // 开始索引
    const startIndex = computed(() => visibleRange.value.startIndex);

    // 偏移量
    const offsetY = computed(() => visibleRange.value.offsetY);

    // 总高度
    const totalHeight = computed(() => visibleRange.value.totalHeight);

    // 获取项目键值
    const getItemKey = (item, index) => {
      if (typeof item === 'object' && item !== null) {
        return item[props.keyField] || index;
      }
      return index;
    };

    // 节流的滚动处理函数
    const throttledHandleScroll = throttle((event) => {
      const container = event.target;
      scrollTop.value = container.scrollTop;
      
      // 检查是否接近底部
      const scrollHeight = container.scrollHeight;
      const clientHeight = container.clientHeight;
      const currentScrollTop = container.scrollTop;
      
      isNearBottom.value = (scrollHeight - clientHeight - currentScrollTop) < 100;
      
      // 发出滚动事件
      emit('scroll', {
        scrollTop: currentScrollTop,
        scrollHeight,
        clientHeight,
        isNearBottom: isNearBottom.value
      });
      
      // 发出可见范围变化事件
      emit('visible-range-change', visibleRange.value);
      
      // 如果接近底部且有更多数据，触发加载更多
      if (isNearBottom.value && props.hasMore && !props.loading) {
        emit('load-more');
      }
    }, 16); // 约60fps

    const handleScroll = throttledHandleScroll;

    // 滚动到指定位置
    const scrollTo = (position) => {
      if (scrollContainer.value) {
        scrollContainer.value.scrollTop = position;
      }
    };

    // 滚动到指定项目
    const scrollToItem = (index) => {
      const position = index * props.itemHeight;
      scrollTo(position);
    };

    // 滚动到顶部
    const scrollToTop = () => {
      scrollTo(0);
    };

    // 滚动到底部
    const scrollToBottom = () => {
      if (scrollContainer.value) {
        scrollTo(scrollContainer.value.scrollHeight);
      }
    };

    // 监听项目变化，自动滚动到顶部（可选）
    watch(() => props.items.length, (newLength, oldLength) => {
      // 如果是新增项目且当前在顶部，保持在顶部
      if (newLength > oldLength && scrollTop.value < 50) {
        nextTick(() => {
          scrollToTop();
        });
      }
    });

    // 监听容器高度变化
    watch(() => props.containerHeight, (newHeight) => {
      virtualScrollManager.options.containerHeight = newHeight;
    });

    // 监听项目高度变化
    watch(() => props.itemHeight, (newHeight) => {
      virtualScrollManager.options.itemHeight = newHeight;
    });

    // 监听缓冲区变化
    watch(() => props.buffer, (newBuffer) => {
      virtualScrollManager.options.buffer = newBuffer;
    });

    onMounted(() => {
      // 初始化滚动位置
      if (scrollContainer.value) {
        scrollTop.value = scrollContainer.value.scrollTop;
      }
    });

    onBeforeUnmount(() => {
      // 清理事件监听器
      if (scrollContainer.value) {
        scrollContainer.value.removeEventListener('scroll', handleScroll);
      }
    });

    return {
      scrollContainer,
      visibleItems,
      startIndex,
      offsetY,
      totalHeight,
      isNearBottom,
      getItemKey,
      handleScroll,
      scrollTo,
      scrollToItem,
      scrollToTop,
      scrollToBottom
    };
  }
};
</script>

<style scoped>
.virtual-scroll-container {
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
}

.virtual-scroll-spacer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  pointer-events: none;
}

.virtual-scroll-content {
  position: absolute;
  width: 100%;
}

.virtual-scroll-item {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #eee;
}

.virtual-scroll-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  font-size: 0.875rem;
  color: #666;
}

/* 滚动条样式 */
.virtual-scroll-container::-webkit-scrollbar {
  width: 8px;
}

.virtual-scroll-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.virtual-scroll-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.virtual-scroll-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .virtual-scroll-container::-webkit-scrollbar {
    width: 6px;
  }
  
  .virtual-scroll-loading {
    font-size: 0.75rem;
    padding: 8px 12px;
  }
}
</style> 