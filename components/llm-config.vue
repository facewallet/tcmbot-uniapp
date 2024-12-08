<template>
  <view class="llm-config-modal">
    <radio-group v-model="selectedModel">
      <label>
        <radio value="model1" />模型1
      </label>
      <label>
        <radio value="model2" />模型2
      </label>
      <!-- 可以添加更多单选选项 -->
    </radio-group>
    <button @click="confirm">确定</button>
  </view>
</template>

<script>
  export default {
    data() {
      return {
        selectedModel: '' // 用于绑定单选按钮选中的值
      };
    },
    methods: {
      confirm() {
        this.$emit('confirm', this.selectedModel); // 触发confirm事件，将选中的值传递给父组件
      }
    }
  };
</script>

<style scoped>
 .llm-config-modal {
    /* 可以添加一些样式来美化模态框的显示效果，比如设置背景色、位置、大小等 */
    background-color: white;
    padding: 20px;
    border-radius: 10px;
  }
</style>