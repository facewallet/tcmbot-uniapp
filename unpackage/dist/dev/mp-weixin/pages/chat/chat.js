"use strict";
const common_vendor = require("../../common/vendor.js");
const common_assets = require("../../common/assets.js");
const _sfc_main = {
  data() {
    return {
      dialogueList: [],
      inputMessage: "",
      websocket: null,
      websocketConnected: false,
      scrollTop: 0
      // Add scrollTop to data
    };
  },
  methods: {
    scrollChatToBottom() {
      this.scrollTop = this.$refs.chat.scrollHeight;
    },
    connectWebSocket() {
      if (this.websocketConnected)
        return;
      this.websocket = common_vendor.index.connectSocket({
        url: "ws://localhost:8086/api/socket/dialogue",
        success: () => {
          console.log("WebSocket connected");
        }
      });
      this.websocket.onOpen(() => {
        this.websocketConnected = true;
      });
      this.websocket.onMessage((message) => {
        const res2 = JSON.parse(message.data);
        console.log("收到的消息：");
        console.log(res2);
        const {
          meta,
          data
        } = res2;
        if (meta.code === 0) {
          const data2 = res2.data;
          if (data2.dialogue) {
            this.dialogueList.push(data2.dialogue);
          }
          if (data2.dialogueList) {
            this.dialogueList.push(...data2.dialogueList);
          }
          this.$nextTick(() => {
            this.scrollChatToBottom();
          });
        }
      });
      this.websocket.onError((error) => {
        console.error("WebSocket error:", error);
        this.websocketConnected = false;
      });
      this.websocket.onClose(() => {
        console.log("WebSocket closed");
        this.websocketConnected = false;
        if (res.meta.code === 0) {
          const data = res.data;
          if (data.dialogue) {
            this.dialogueList.push(data.dialogue);
          }
          if (data.dialogueList) {
            this.dialogueList.push(...data.dialogueList);
          }
        }
      });
      this.websocket.onError((error) => {
        console.error("WebSocket error:", error);
        this.websocketConnected = false;
      });
      this.websocket.onClose(() => {
        console.log("WebSocket closed");
        this.websocketConnected = false;
      });
    },
    fetchData() {
      common_vendor.index.request({
        url: "/api/pub/init/welcome",
        success: (res2) => {
          console.log(res2);
          if (res2.data.meta.code === 0) {
            const data = res2.data.data;
            if (data.dialogueList) {
              this.dialogueList.push(...data.dialogueList);
            }
            if (data.dialogue) {
              this.dialogueList.push(data.dialogue);
            }
          }
        },
        fail: (err) => {
          console.error(err);
        }
      });
    },
    submitForm(dialogue) {
      common_vendor.index.request({
        url: "/api/pub/dialogue",
        method: "POST",
        data: dialogue,
        success: (res2) => {
          console.log("Form submitted successfully:", res2);
        },
        fail: (err) => {
          console.error("Form submission failed:", err);
        }
      });
    },
    submitSocketForm(dialogue) {
      let cloneDialogue = JSON.parse(JSON.stringify(dialogue));
      cloneDialogue.speaker = "user";
      this.dialogueList.push(cloneDialogue);
      if (this.websocketConnected) {
        this.websocket.send({
          data: JSON.stringify(cloneDialogue),
          success: () => {
            console.log("Form sent successfully");
            this.$nextTick(() => {
              this.scrollChatToBottom();
            });
          },
          fail: (err) => {
            console.error("Failed to send form:", err);
          }
        });
      } else {
        this.connectWebSocket();
        this.websocket.onOpen(() => {
          this.websocket.send({
            data: JSON.stringify(cloneDialogue),
            success: () => {
              console.log("Form sent successfully after connection");
              this.$nextTick(() => {
                this.scrollChatToBottom();
              });
            },
            fail: (err) => {
              console.error("Failed to send form after connection:", err);
            }
          });
        });
      }
    },
    radioChange(formItem, value) {
      console.log(formItem);
      console.log("value=" + value);
      formItem.value = value;
    },
    radioGroupChange(e, formItem) {
      console.log("radioGroup" + formItem);
      formItem.value = e.detail.value;
    },
    checkboxChange(formItem, value) {
      if (!formItem.values) {
        formItem.values = [];
      }
      const index = formItem.values.indexOf(value);
      if (index === -1) {
        formItem.values.push(value);
      } else {
        formItem.values.splice(index, 1);
      }
    },
    uploadFile() {
    },
    sendMessage() {
      this.dialogueList.push({
        speaker: "user",
        type: "text",
        content: this.inputMessage
      });
      this.inputMessage = "";
    },
    sendSocketMessage() {
      if (this.inputMessage.trim() === "")
        return;
      const message = {
        speaker: "user",
        type: "text",
        content: this.inputMessage,
        user_intent: "user_ask"
      };
      this.dialogueList.push(message);
      this.inputMessage = "";
      if (this.websocketConnected) {
        this.websocket.send({
          data: JSON.stringify(message),
          success: () => {
            console.log("Message sent successfully");
            this.$nextTick(() => {
              this.scrollChatToBottom();
            });
          },
          fail: (err) => {
            console.error("Failed to send message:", err);
          }
        });
      } else {
        this.connectWebSocket();
        this.websocket.onOpen(() => {
          this.websocket.send({
            data: JSON.stringify(message),
            success: () => {
              console.log("Message sent successfully after connection");
            },
            fail: (err) => {
              console.error("Failed to send message after connection:", err);
            }
          });
        });
      }
      this.inputMessage = "";
    }
  },
  watch: {
    dialogueList() {
      this.$nextTick(() => {
        this.scrollChatToBottom();
      });
    }
  },
  mounted() {
    this.fetchData();
    this.connectWebSocket();
    this.scrollChatToBottom();
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: common_assets._imports_0,
    b: common_vendor.f($data.dialogueList, (dialogue, index, i0) => {
      return common_vendor.e({
        a: dialogue.speaker === "bot" ? "/static/bot.png" : "/static/user.png",
        b: dialogue.type === "text"
      }, dialogue.type === "text" ? {
        c: common_vendor.t(dialogue.content)
      } : {}, {
        d: dialogue.type === "form"
      }, dialogue.type === "form" ? {
        e: common_vendor.f(dialogue.forms, (formItem, k1, i1) => {
          return common_vendor.e({
            a: common_vendor.t(formItem.label),
            b: formItem.type === "text" || formItem.type === "password"
          }, formItem.type === "text" || formItem.type === "password" ? {
            c: formItem.type,
            d: formItem.placeholder,
            e: formItem.required === "true",
            f: formItem.value,
            g: common_vendor.o(($event) => formItem.value = $event.detail.value, formItem.id)
          } : {}, {
            h: formItem.type === "radio"
          }, formItem.type === "radio" ? {
            i: common_vendor.f(formItem.options, (option, k2, i2) => {
              return {
                a: option.value,
                b: formItem.value === option.value,
                c: common_vendor.o(($event) => $options.radioChange(formItem, option.value), option.id),
                d: common_vendor.t(option.label),
                e: option.id
              };
            }),
            j: common_vendor.o(($event) => $options.radioGroupChange($event, formItem), formItem.id)
          } : {}, {
            k: formItem.type === "checkbox"
          }, formItem.type === "checkbox" ? {
            l: common_vendor.f(formItem.options, (option, k2, i2) => {
              return {
                a: option.value,
                b: formItem.values && formItem.values.includes(option.value),
                c: common_vendor.o(($event) => $options.checkboxChange(formItem, option.value), option.id),
                d: common_vendor.t(option.label),
                e: option.id
              };
            })
          } : {}, {
            m: formItem.type === "file"
          }, formItem.type === "file" ? {
            n: common_assets._imports_1,
            o: common_vendor.o((...args) => $options.uploadFile && $options.uploadFile(...args), formItem.id)
          } : {}, {
            p: formItem.id
          });
        }),
        f: common_vendor.o(($event) => $options.submitSocketForm(dialogue), index)
      } : {}, {
        g: dialogue.speaker === "user" ? "#ffffff" : "#f8f8f8",
        h: index,
        i: dialogue.speaker === "bot" ? 1 : "",
        j: dialogue.speaker === "user" ? 1 : ""
      });
    }),
    c: $data.scrollTop,
    d: common_vendor.o((...args) => $options.scrollChatToBottom && $options.scrollChatToBottom(...args)),
    e: common_vendor.o((...args) => $options.sendSocketMessage && $options.sendSocketMessage(...args)),
    f: $data.inputMessage,
    g: common_vendor.o(($event) => $data.inputMessage = $event.detail.value),
    h: common_vendor.o((...args) => $options.sendSocketMessage && $options.sendSocketMessage(...args))
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
