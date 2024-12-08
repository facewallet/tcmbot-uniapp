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
      // 使聊天窗口滚动到指定元素id的值
      scrollIntoView: "",
      // 消息列表数据
      msgList: [],
      // 通讯请求状态
      requestState: 0,
      //0发送中 100发送成功 -100发送失败
      // 本地对话是否因积分不足而终止
      insufficientScore: false,
      // 输入框的消息内容
      content: "",
      // 记录流式响应次数
      sseIndex: 0,
      // 是否启用流式响应模式
      enableStream: true,
      // 当前屏幕是否为宽屏
      isWidescreen: false,
      keyboardHeight: 0,
      showLlmConfig: false,
      // 控制llm-config组件是否显示，初始为隐藏
      llmModel: "tcm-all",
      showModelPopup: false,
      // 控制单选组件弹窗是否显示，初始为隐藏
      modelOptions: [
        {
          name: "全部模型",
          value: "tcm-all",
          checked: true,
          disabled: false
        },
        {
          name: "中医大模型",
          value: "tcm-rag",
          checked: false,
          disabled: false
        },
        {
          name: "中医小模型",
          value: "tcm-ner",
          checked: false,
          disabled: false
        },
        {
          name: "中医知识图谱",
          value: "tcm-graphrag",
          checked: false,
          disabled: false
        },
        {
          name: "中医智能体",
          value: "tcm-agent",
          checked: false,
          disabled: true
        },
        {
          name: "中医介子推",
          value: "tcm-jzt",
          checked: false,
          disabled: true
        }
      ],
      // 存储从接口获取的单选选项数据，格式如 [{name: '选项1', value: 'option1'},...]
      selectedModel: ""
      // 用于绑定单选按钮选中的值
    };
  },
  computed: {
    // 输入框是否禁用
    inputBoxDisabled() {
      if (this.sseIndex !== 0) {
        return true;
      }
      return !!(this.msgList.length && this.msgList.length % 2 !== 0);
    },
    // 获取当前环境
    NODE_ENV() {
      return "development";
    },
    footBoxPaddingBottom() {
      return (this.keyboardHeight || 10) + "px";
    }
  },
  // 监听msgList变化，将其存储到本地缓存中
  watch: {
    llmModel(llmModel) {
      common_vendor.index.setStorage({
        key: "uni-ai-chat-llmModel",
        data: llmModel
      });
    }
  },
  beforeMount() {
  },
  async mounted() {
    this.fetchWelcome();
    this.fetchChannel();
    this.connectWebSocket();
    this.llmModel = common_vendor.index.getStorageSync("uni-ai-chat-llmModel");
    this.$nextTick(() => {
      this.showLastMsg();
    });
    common_vendor.index.onKeyboardHeightChange((e) => {
      this.keyboardHeight = e.height;
      this.$nextTick(() => {
        this.showLastMsg();
      });
    });
  },
  methods: {
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
    },
    fetchWelcome() {
      common_vendor.index.request({
        url: "http://localhost:8086/api/pub/dialogue/welcome",
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
    fetchChannel() {
      common_vendor.index.request({
        url: "http://localhost:8086/api/pub/dialogue/channel",
        success: (res2) => {
          console.log(res2);
          if (res2.data.meta.code === 0) {
            const data = res2.data.data;
            this.modelOptions = data.channelList;
          }
        },
        fail: (err) => {
          console.error(err);
        }
      });
    },
    // radioChange(formItem, value) {
    // 	console.log(formItem)
    // 	console.log('value=' + value)
    // 	formItem.value = value;
    // },
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
    submitSocketForm(dialogue) {
      let cloneDialogue = JSON.parse(JSON.stringify(dialogue));
      cloneDialogue.speaker = "user";
      this.dialogueList.push(cloneDialogue);
      if (this.websocketConnected) {
        this.websocket.send({
          data: JSON.stringify(cloneDialogue),
          success: () => {
            console.log("Form sent successfully");
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
            },
            fail: (err) => {
              console.error("Failed to send form after connection:", err);
            }
          });
        });
      }
    },
    setLLMmodel() {
      this.showModelPopup = true;
    },
    confirmModel() {
      console.log("Selected llmModel:", this.llmModel);
      console.log("Selected selectedModel:", this.selectedModel);
      this.showModelPopup = false;
    },
    // setLLMmodel() {
    // 	this.showLlmConfig = true; // 点击设置按钮时，显示llm-config组件
    // },
    radioChange(e) {
      this.llmModel = e.detail.value;
    },
    handleConfirm(modelValue) {
      this.llmModel = modelValue;
      this.showLlmConfig = false;
    },
    // setLLMmodel() {
    // 	this.$refs['llm-config'].open(model => {
    // 		console.log('model', model);
    // 		this.llmModel = model
    // 	})
    // },
    // 更新最后一条消息
    updateLastMsg(param) {
      let length = this.msgList.length;
      if (length === 0) {
        return;
      }
      let lastMsg = this.msgList[length - 1];
      if (typeof param == "function") {
        let callback = param;
        callback(lastMsg);
      } else {
        const [data, cover = false] = arguments;
        if (cover) {
          lastMsg = data;
        } else {
          lastMsg = Object.assign(lastMsg, data);
        }
      }
      this.msgList.splice(length - 1, 1, lastMsg);
    },
    // 滚动窗口以显示最新的一条消息
    showLastMsg() {
      this.$nextTick(() => {
        this.scrollIntoView = "last-msg-item";
        this.$nextTick(() => {
          this.scrollIntoView = "";
        });
      });
    }
  }
};
if (!Array) {
  const _easycom_uni_icons2 = common_vendor.resolveComponent("uni-icons");
  _easycom_uni_icons2();
}
const _easycom_uni_icons = () => "../../uni_modules/uni-icons/components/uni-icons/uni-icons.js";
if (!Math) {
  _easycom_uni_icons();
}
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.f($data.dialogueList, (dialogue, index, i0) => {
      return common_vendor.e({
        a: dialogue.speaker === "bot"
      }, dialogue.speaker === "bot" ? {
        b: "2d878ce0-0-" + i0,
        c: common_vendor.p({
          color: "#ff5100",
          type: "headphones",
          size: "30"
        })
      } : {
        d: "2d878ce0-1-" + i0,
        e: common_vendor.p({
          color: "#ff5100",
          type: "contact",
          size: "30"
        })
      }, {
        f: dialogue.type === "text"
      }, dialogue.type === "text" ? {
        g: common_vendor.t(dialogue.content)
      } : {}, {
        h: dialogue.type === "form"
      }, dialogue.type === "form" ? {
        i: common_vendor.f(dialogue.forms, (formItem, k1, i1) => {
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
                c: common_vendor.t(option.label),
                d: option.id
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
        j: common_vendor.o(($event) => $options.submitSocketForm(dialogue), index)
      } : {}, {
        k: dialogue.speaker === "user" ? "#ffffff" : "#f8f8f8",
        l: index,
        m: dialogue.speaker === "bot" ? 1 : "",
        n: dialogue.speaker === "user" ? 1 : ""
      });
    }),
    b: $data.scrollIntoView,
    c: !$data.isWidescreen
  }, !$data.isWidescreen ? {
    d: common_vendor.o($options.setLLMmodel),
    e: common_vendor.p({
      color: "#ff5100",
      size: "20px",
      type: "bars"
    })
  } : {}, {
    f: !$data.isWidescreen,
    g: -1,
    h: $data.inputMessage,
    i: common_vendor.o(($event) => $data.inputMessage = $event.detail.value),
    j: common_vendor.o($options.sendSocketMessage),
    k: common_vendor.p({
      color: "#ff5100",
      type: "paperplane-filled",
      size: "30"
    }),
    l: $data.msgList.length && $data.msgList.length % 2 !== 0 ? "ai正在回复中不能发送" : "",
    m: $options.footBoxPaddingBottom,
    n: $data.showModelPopup
  }, $data.showModelPopup ? {
    o: common_vendor.f($data.modelOptions, (option, index, i0) => {
      return {
        a: option.value,
        b: option.disabled === "YES",
        c: option.value === this.llmModel,
        d: common_vendor.t(option.name),
        e: index
      };
    }),
    p: common_vendor.o((...args) => $options.radioChange && $options.radioChange(...args)),
    q: common_vendor.o((...args) => $options.confirmModel && $options.confirmModel(...args))
  } : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
