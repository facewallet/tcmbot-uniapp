export default {
  created() {
    //#ifdef MP-WEIXIN
    wx.showShareMenu({
      withShareTicket: true,
      menus: ["shareAppMessage", "shareTimeline"],
    });
    //#endif
  },
  onShareAppMessage(res) {
    // 发送给朋友
    return {
      title: "中医大模型", 
      imageUrl: "/static/tcmbot.png"
    };
  },
  onShareTimeline(res) {
    // 分享到朋友圈2
    return {
      title: "中医大模型", 
      imageUrl: "/static/logo.png"
    };
  },
};
