"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      dialogue: {
        formList: []
      }
    };
  },
  created() {
    this.fetchDialogue();
  },
  methods: {
    fetchDialogue() {
      common_vendor.index.request({
        url: "/api/pub/dialogue",
        success: (res) => {
          if (res.data && res.data.type === "form") {
            this.dialogue = res.data;
          }
        },
        fail: (err) => {
          console.error("Failed to fetch dialogue:", err);
        }
      });
    },
    handleRadioChange(value, field) {
      field.value = value.detail.value;
    },
    handleCheckboxChange(value, field) {
      field.values = value.detail.value;
    },
    handleFileChange(event, field) {
      const file = event.target.files[0];
      field.value = file;
    },
    handleButtonClick(value) {
      console.log("Button clicked:", value);
    },
    handleSubmit(event) {
      event.preventDefault();
      const formData = new FormData();
      this.dialogue.formList.forEach((field) => {
        if (field.type === "file") {
          formData.append(field.label, field.value);
        } else {
          formData.append(field.label, field.value || "");
        }
      });
      common_vendor.index.request({
        url: "/api/pub/dialogue",
        method: "POST",
        data: JSON.stringify(this.dialogue),
        header: {
          "Content-Type": "application/json"
        },
        success: (res) => {
          console.log("Form submitted successfully:", res);
        },
        fail: (err) => {
          console.error("Failed to submit form:", err);
        }
      });
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: common_vendor.f($data.dialogue.formList, (field, k0, i0) => {
      return common_vendor.e({
        a: common_vendor.t(field.label),
        b: field.type === "text"
      }, field.type === "text" ? {
        c: field.placeholder,
        d: field.label,
        e: field.required === "true",
        f: field.value,
        g: common_vendor.o(($event) => field.value = $event.detail.value, field.id)
      } : {}, {
        h: field.type === "password"
      }, field.type === "password" ? {
        i: field.placeholder,
        j: field.label,
        k: field.required === "true",
        l: field.value,
        m: common_vendor.o(($event) => field.value = $event.detail.value, field.id)
      } : {}, {
        n: field.type === "radio"
      }, field.type === "radio" ? {
        o: common_vendor.f(field.options, (option, k1, i1) => {
          return common_vendor.e({
            a: option.value,
            b: field.value === option.value,
            c: option.type === "button"
          }, option.type === "button" ? {
            d: common_vendor.t(option.label),
            e: common_vendor.o(($event) => $options.handleButtonClick(option.value), option.id)
          } : option.type === "text" ? {
            g: option.placeholder,
            h: option.value,
            i: common_vendor.o(($event) => option.value = $event.detail.value, option.id)
          } : {
            j: common_vendor.t(option.label)
          }, {
            f: option.type === "text",
            k: option.id
          });
        }),
        p: common_vendor.o((value) => $options.handleRadioChange(value, field), field.id)
      } : {}, {
        q: field.type === "checkbox"
      }, field.type === "checkbox" ? {
        r: common_vendor.f(field.options, (option, k1, i1) => {
          return {
            a: option.value,
            b: field.values && field.values.includes(option.value),
            c: common_vendor.t(option.label),
            d: option.id
          };
        }),
        s: common_vendor.o((value) => $options.handleCheckboxChange(value, field), field.id)
      } : {}, {
        t: field.type === "file"
      }, field.type === "file" ? {
        v: common_vendor.o((event) => $options.handleFileChange(event, field), field.id),
        w: field.label,
        x: field.required === "true"
      } : {}, {
        y: field.id
      });
    }),
    b: common_vendor.o((...args) => $options.handleSubmit && $options.handleSubmit(...args))
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
