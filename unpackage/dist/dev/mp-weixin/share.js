"use strict";
const common_vendor = require("./common/vendor.js");
const share = {
  created() {
    common_vendor.wx$1.showShareMenu({
      withShareTicket: true,
      menus: ["shareAppMessage", "shareTimeline"]
    });
  },
  onShareAppMessage(res) {
    return {
      title: "中医大模型",
      imageUrl: "/static/tcmbot.png"
    };
  },
  onShareTimeline(res) {
    return {
      title: "中医大模型",
      imageUrl: "/static/logo.png"
    };
  }
};
exports.share = share;
