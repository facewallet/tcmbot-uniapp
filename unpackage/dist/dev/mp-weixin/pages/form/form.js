"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      dialogue: null
    };
  },
  methods: {
    radioChange(e, item) {
      item.value = e.detail.value;
    },
    checkboxChange(e, item) {
      item.values = e.detail.value;
    },
    handleFileUpload(item) {
    },
    handleSubmit(e) {
      common_vendor.index.request({
        url: "/api/pub/dialogue",
        method: "POST",
        data: this.dialogue,
        success: (res) => {
          console.log("Form submitted successfully:", res);
        },
        fail: (err) => {
          console.error("Form submission failed:", err);
        }
      });
    },
    fetchDialogue() {
      common_vendor.index.request({
        url: "/api/pub/dialogue",
        method: "GET",
        success: (res) => {
          if (res.data && res.data.type === "form") {
            this.dialogue = res.data;
          }
        },
        fail: (err) => {
          console.error("Failed to fetch dialogue:", err);
        }
      });
    }
  },
  mounted() {
    this.fetchDialogue();
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: $data.dialogue && $data.dialogue.type === "form"
  }, $data.dialogue && $data.dialogue.type === "form" ? {
    b: common_vendor.f($data.dialogue.formList, (item, k0, i0) => {
      return common_vendor.e({
        a: item.type === "text"
      }, item.type === "text" ? {
        b: item.placeholder,
        c: item.label,
        d: item.required === "true",
        e: item.value,
        f: common_vendor.o(($event) => item.value = $event.detail.value, item.id)
      } : item.type === "password" ? {
        h: item.placeholder,
        i: item.label,
        j: item.required === "true",
        k: item.value,
        l: common_vendor.o(($event) => item.value = $event.detail.value, item.id)
      } : item.type === "radio" ? {
        n: common_vendor.f(item.options, (option, k1, i1) => {
          return {
            a: option.value,
            b: item.value === option.value,
            c: common_vendor.t(option.label),
            d: option.id
          };
        }),
        o: common_vendor.o(($event) => $options.radioChange($event, item), item.id)
      } : item.type === "checkbox" ? {
        q: common_vendor.f(item.options, (option, k1, i1) => {
          return {
            a: option.value,
            b: item.values && item.values.includes(option.value),
            c: common_vendor.t(option.label),
            d: option.id
          };
        }),
        r: common_vendor.o(($event) => $options.checkboxChange($event, item), item.id)
      } : item.type === "file" ? {
        t: common_vendor.o(($event) => $options.handleFileUpload(item), item.id)
      } : {}, {
        g: item.type === "password",
        m: item.type === "radio",
        p: item.type === "checkbox",
        s: item.type === "file",
        v: item.id
      });
    }),
    c: common_vendor.o((...args) => $options.handleSubmit && $options.handleSubmit(...args))
  } : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
