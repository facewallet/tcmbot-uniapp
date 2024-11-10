<template>
  <view>
    <form @submit="handleSubmit" v-if="dialogue && dialogue.type === 'form'">
      <view class="form-item" v-for="item in dialogue.formList" :key="item.id">
        <!-- 文本输入框 -->
        <input v-if="item.type === 'text'" :placeholder="item.placeholder" v-model="item.value" :name="item.label" :required="item.required === 'true'"/>
        
        <!-- 密码输入框 -->
        <input v-else-if="item.type === 'password'" :placeholder="item.placeholder" type="password" v-model="item.value" :name="item.label" :required="item.required === 'true'"/>
        
        <!-- 单选框 -->
        <radio-group v-else-if="item.type === 'radio'" @change="radioChange($event, item)">
          <label v-for="option in item.options" :key="option.id">
            <radio :value="option.value" :checked="item.value === option.value"/>{{option.label}}
          </label>
        </radio-group>
        
        <!-- 多选框 -->
        <checkbox-group v-else-if="item.type === 'checkbox'" @change="checkboxChange($event, item)">
          <label v-for="option in item.options" :key="option.id">
            <checkbox :value="option.value" :checked="item.values && item.values.includes(option.value)"/>{{option.label}}
          </label>
        </checkbox-group>
        
        <!-- 文件上传 -->
        <button v-else-if="item.type === 'file'" @click="handleFileUpload(item)">上传文件</button>
      </view>
      <button form-type="submit">提交</button>
    </form>
  </view>
</template>

<script>
export default {
  data() {
    return {
      dialogue: null
    }
  },
  methods: {
    radioChange(e, item) {
      item.value = e.detail.value;
    },
    checkboxChange(e, item) {
      item.values = e.detail.value;
    },
    handleFileUpload(item) {
      // 文件上传逻辑
      // uni.chooseImage 或其他文件选择API
    },
    handleSubmit(e) {
      // e.preventDefault();
      uni.request({
        url: '/api/pub/dialogue',
        method: 'POST',
        data: this.dialogue,
        success: (res) => {
          // 处理成功响应
          console.log('Form submitted successfully:', res);
        },
        fail: (err) => {
          // 处理失败响应
          console.error('Form submission failed:', err);
        }
      });
    },
    fetchDialogue() {
      uni.request({
        url: '/api/pub/dialogue',
        method: 'GET',
        success: (res) => {
          if (res.data && res.data.type === 'form') {
            this.dialogue = res.data;
          }
        },
        fail: (err) => {
          console.error('Failed to fetch dialogue:', err);
        }
      });
    }
  },
  mounted() {
    this.fetchDialogue();
  }
}
</script>

<style>
.form-item {
  margin-bottom: 20px;
}
</style>
