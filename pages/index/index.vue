<template>
  <view class="content">
    <image class="logo" src="/static/logo.png"></image>
    <view class="text-area">
      <text class="title">{{ title }}</text>
    </view>
    <text>{{ response }}</text> <!-- 添加一个文本标签来显示响应数据 -->
  </view>
</template>

<script>
export default {
  data() {
    return {
      title: 'Hello SuanSuan2',
      response: '2' // 添加一个属性来存储响应数据
    };
  },
  onLoad() {
    this.fetchData(); // 在页面加载时调用 fetchData 方法
  },
  methods: {
    fetchData() {
      uni.request({
        url: '/api/pub/echo', // 请求的URL
        method: 'GET', // 请求方法，根据实际情况选择GET或POST
        success: (res) => {
          // 请求成功后的处理
          if (res.statusCode === 200) {
            this.response = res.data;
          } else {
            console.error('请求失败', res);
          }
        },
        fail: (err) => {
          // 请求失败后的处理
          console.error('请求失败', err);
        }
      });
    }
  }
};
</script>

<style>
.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.logo {
  height: 200rpx;
  width: 200rpx;
  margin-top: 200rpx;
  margin-left: auto;
  margin-right: auto;
  margin-bottom: 50rpx;
}

.text-area {
  display: flex;
  justify-content: center;
}

.title {
  font-size: 36rpx;
  color: #8f8f94;
}
</style>