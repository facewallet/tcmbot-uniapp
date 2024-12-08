<template>
	<view class="container">
		<!-- #ifdef H5 -->
		<view v-if="isWidescreen" class="header">中医机器人Web版</view>
		<!-- #endif -->
		<!-- <text class="noData" v-if="msgList.length === 0">没有对话记录</text> -->
		<scroll-view :scroll-into-view="scrollIntoView" scroll-y="true" class="msg-list" :enable-flex="true">
			<view v-for="(dialogue, index) in dialogueList" :key="index" class="dialogue"
				:class="{ 'bot-speak': dialogue.speaker === 'bot', 'user-speak': dialogue.speaker === 'user' }">
				<image :src="dialogue.speaker === 'bot' ? '/static/bot.png' : '/static/user.png'" class="avatar" />
				<view class="message" :style="{ backgroundColor: dialogue.speaker === 'user' ? '#ffffff' : '#f8f8f8' }">
					<text v-if="dialogue.type === 'text'">{{ dialogue.content }}</text>
					<form v-if="dialogue.type === 'form'" @submit="submitSocketForm(dialogue)">
						<view v-for="formItem in dialogue.forms" :key="formItem.id">
							<label>{{formItem.label}}</label>
							<input v-if="formItem.type === 'text' || formItem.type === 'password'" :type="formItem.type"
								:placeholder="formItem.placeholder" v-model="formItem.value"
								:required="formItem.required === 'true'" />
							<radio-group v-if="formItem.type === 'radio'" @change="radioGroupChange($event,formItem)">
								<label v-for="option in formItem.options" :key="option.id">
									<radio :value="option.value" :checked="formItem.value === option.value"
										@change="radioChange(formItem, option.value)" style="color: #ff5100;" />
									{{ option.label }}
								</label>
							</radio-group>
							<checkbox-group v-if="formItem.type === 'checkbox'">
								<label v-for="option in formItem.options" :key="option.id">
									<checkbox :value="option.value"
										:checked="formItem.values && formItem.values.includes(option.value)"
										@change="checkboxChange(formItem, option.value)" style="color: #ff5100;" />
									{{ option.label }}
								</label>
							</checkbox-group>
							<button v-if="formItem.type === 'file'" @click="uploadFile" class="upload-button">
								<image src="/static/upload.png" class="upload-icon" />
							</button>
						</view>
						<button form-type="submit" class="submit-button">提交</button>
					</form>
				</view>
			</view>

			<view id="last-msg-item" style="height: 1px;"></view>
		</scroll-view>

		<view class="foot-box" :style="{'padding-bottom':footBoxPaddingBottom}">
			<!-- #ifdef H5 -->
			<view class="pc-menu" v-if="isWidescreen">
				<view class="settings pc-menu-item" @click="setLLMmodel" title="设置">
					<uni-icons color="#555" size="20px" type="settings"></uni-icons>
				</view>
			</view>
			<!-- #endif -->
			<view class="foot-box-content">
				<view v-if="!isWidescreen" class="menu">
					<uni-icons class="menu-item" @click="setLLMmodel" color="#555" size="20px"
						type="settings"></uni-icons>
				</view>
				<view class="textarea-box">
					<textarea v-model="inputMessage" :cursor-spacing="15" class="textarea" :auto-height="!isWidescreen"
						placeholder="请输入要发给中医机器人的内容" :maxlength="-1" :adjust-position="false"
						:disable-default-padding="false" placeholder-class="input-placeholder"></textarea>
				</view>
				<view class="send-btn-box" :title="(msgList.length && msgList.length%2 !== 0) ? 'ai正在回复中不能发送':''">
					<!-- #ifdef H5 -->
					<text v-if="isWidescreen" class="send-btn-tip">↵ 发送 / shift + ↵ 换行</text>
					<!-- #endif -->
					<button @click="sendSocketMessage" class="send" type="primary">发送</button>
				</view>
			</view>
		</view>
		<view class="model-popup" v-if="showModelPopup"
			:style="{ display: showModelPopup? 'flex' : 'none', justifyContent: 'center', alignItems: 'center' }">
			<view class="popup-content">
				<radio-group v-model="selectedModel">
					<view class="option-item" v-for="(option, index) in modelOptions" :key="index">
						<radio :value="option.value" />
						<text class="option-text">{{ option.name }}</text>
					</view>
				</radio-group>
				<button @click="confirmModel">确定</button>
			</view>
		</view>
	</view>
</template>

<script>
	// 键盘的shift键是否被按下
	let shiftKeyPressed = false

	export default {
		data() {
			return {
				dialogueList: [],
				inputMessage: '',
				websocket: null,
				websocketConnected: false,
				// 使聊天窗口滚动到指定元素id的值
				scrollIntoView: "",
				// 消息列表数据
				msgList: [],
				// 通讯请求状态
				requestState: 0, //0发送中 100发送成功 -100发送失败
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

				// llmModel: false,
				keyboardHeight: 0,
				showLlmConfig: false, // 控制llm-config组件是否显示，初始为隐藏
				llmModel: '',
				showModelPopup: false, // 控制单选组件弹窗是否显示，初始为隐藏
				modelOptions: [{
					name: '选项1',
					value: 'option1'
				}, {
					name: '选项1',
					value: 'option1'
				}], // 存储从接口获取的单选选项数据，格式如 [{name: '选项1', value: 'option1'},...]
				selectedModel: '' // 用于绑定单选按钮选中的值
			}
		},
		computed: {
			// 输入框是否禁用
			inputBoxDisabled() {
				// 如果正在等待流式响应，则禁用输入框
				if (this.sseIndex !== 0) {
					return true
				}
				// 如果消息列表长度为奇数，则禁用输入框
				return !!(this.msgList.length && this.msgList.length % 2 !== 0)
			},
			// 获取当前环境
			NODE_ENV() {
				return process.env.NODE_ENV
			},
			footBoxPaddingBottom() {
				return (this.keyboardHeight || 10) + 'px'
			}
		},
		// 监听msgList变化，将其存储到本地缓存中
		watch: {
			llmModel(llmModel) {
				let title = 'tcmbot'
				if (llmModel) {
					title += ` (${llmModel})`
				}
				// uni.setNavigationBarTitle({title})
				// #ifdef H5
				if (this.isWidescreen) {
					document.querySelector('.header').innerText = title
				}
				// #endif
				uni.setStorage({
					key: 'uni-ai-chat-llmModel',
					data: llmModel
				})
			}
		},
		beforeMount() {
			// #ifdef H5
			// 监听屏幕宽度变化，判断是否为宽屏 并设置isWidescreen的值
			uni.createMediaQueryObserver(this).observe({
				minWidth: 650,
			}, matches => {
				this.isWidescreen = matches;
			})
			// #endif
		},
		async mounted() {
			this.fetchData();
			this.connectWebSocket();
			// 获得之前设置的llmModel
			this.llmModel = uni.getStorageSync('uni-ai-chat-llmModel')


			// this.msgList.pop()
			// console.log('this.msgList', this.msgList);

			// 在dom渲染完毕后 使聊天窗口滚动到最后一条消息
			this.$nextTick(() => {
				this.showLastMsg()
			})

			// #ifdef H5
			//获得消息输入框对象
			let adjunctKeydown = false
			const textareaDom = document.querySelector('.textarea-box textarea');
			if (textareaDom) {
				//键盘按下时
				textareaDom.onkeydown = e => {
					// console.log('onkeydown', e.keyCode)
					if ([16, 17, 18, 93].includes(e.keyCode)) {
						//按下了shift ctrl alt windows键
						adjunctKeydown = true;
					}
					if (e.keyCode == 13 && !adjunctKeydown) {
						e.preventDefault()
						// 执行发送
						setTimeout(() => {
							this.beforeSend();
						}, 300)
					}
				};
				textareaDom.onkeyup = e => {
					//松开adjunct键
					if ([16, 17, 18, 93].includes(e.keyCode)) {
						adjunctKeydown = false;
					}
				};

				// 可视窗口高
				let initialInnerHeight = window.innerHeight;
				if (uni.getSystemInfoSync().platform == "ios") {
					textareaDom.addEventListener('focus', () => {
						let interval = setInterval(function() {
							if (window.innerHeight !== initialInnerHeight) {
								clearInterval(interval)
								// 触发相应的回调函数
								document.querySelector('.container').style.height = window
									.innerHeight + 'px'
								window.scrollTo(0, 0);
								this.showLastMsg()
							}
						}, 1);
					})
					textareaDom.addEventListener('blur', () => {
						document.querySelector('.container').style.height = initialInnerHeight + 'px'
					})
				} else {
					window.addEventListener('resize', (e) => {
						this.showLastMsg()
					})
				}
			}
			// #endif

			// #ifndef H5
			uni.onKeyboardHeightChange(e => {
				this.keyboardHeight = e.height
				// 在dom渲染完毕后 使聊天窗口滚动到最后一条消息
				this.$nextTick(() => {
					this.showLastMsg()
				})
			})
			// #endif
		},
		methods: {
			connectWebSocket() {
				if (this.websocketConnected) return;
				this.websocket = uni.connectSocket({
					url: 'ws://localhost:8086/api/socket/dialogue',
					success: () => {
						console.log('WebSocket connected');
					}
				});

				this.websocket.onOpen(() => {
					this.websocketConnected = true;
				});

				this.websocket.onMessage((message) => {
					const res = JSON.parse(message.data);
					console.log("收到的消息：")
					console.log(res)
					const {
						meta,
						data
					} = res;
					if (meta.code === 0) {
						const data = res.data;
						if (data.dialogue) {
							this.dialogueList.push(data.dialogue);
						}
						if (data.dialogueList) {
							this.dialogueList.push(...data.dialogueList);
						}
						// this.$nextTick(() => {
						// 	this.scrollChatToBottom();
						// });
					}
				});

				this.websocket.onError((error) => {
					console.error('WebSocket error:', error);
					this.websocketConnected = false;
				});

				this.websocket.onClose(() => {
					console.log('WebSocket closed');
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
					console.error('WebSocket error:', error);
					this.websocketConnected = false;
				});

				this.websocket.onClose(() => {
					console.log('WebSocket closed');
					this.websocketConnected = false;
				});
			},
			sendSocketMessage() {
				if (this.inputMessage.trim() === '') return;
				const message = {
					speaker: 'user',
					type: 'text',
					content: this.inputMessage,
					user_intent: 'user_ask'
				};
				this.dialogueList.push(message);
				this.inputMessage = '';
				if (this.websocketConnected) {
					this.websocket.send({
						data: JSON.stringify(message),
						success: () => {
							console.log('Message sent successfully');
							// this.$nextTick(() => {
							// 	this.scrollChatToBottom();
							// });
						},
						fail: (err) => {
							console.error('Failed to send message:', err);
						}
					});
				} else {
					this.connectWebSocket();
					this.websocket.onOpen(() => {
						this.websocket.send({
							data: JSON.stringify(message),
							success: () => {
								console.log('Message sent successfully after connection');
							},
							fail: (err) => {
								console.error('Failed to send message after connection:', err);
							}
						});
					});
				}
				this.inputMessage = '';
			},

			fetchData() {
				uni.request({
					url: '/api/pub/init/welcome',
					success: (res) => {
						console.log(res)
						if (res.data.meta.code === 0) {
							const data = res.data.data;

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
			radioChange(formItem, value) {
				console.log(formItem)
				console.log('value=' + value)
				formItem.value = value;

			},
			radioGroupChange(e, formItem) {
				console.log('radioGroup' + formItem)
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
				// Implement file upload logic here
			},
			submitSocketForm(dialogue) {
				let cloneDialogue = JSON.parse(JSON.stringify(dialogue));
				cloneDialogue.speaker = 'user'
				// if (cloneDialogue.bot_intent === 'do_agent_select') {
				// 	cloneDialogue.user_intent = 'finish_agent_select'
				// } else if (cloneDialogue.bot_intent === 'do_edge_select') {
				// 	cloneDialogue.user_intent = 'finish_edge_select'
				// } else if (cloneDialogue.bot_intent === 'do_slot_fill') {
				// 	cloneDialogue.user_intent = 'finish_slot_fill'
				// }
				this.dialogueList.push(cloneDialogue);
				if (this.websocketConnected) {
					this.websocket.send({
						data: JSON.stringify(cloneDialogue),
						success: () => {
							console.log('Form sent successfully');
							// this.$nextTick(() => {
							// 	this.scrollChatToBottom();
							// });
						},
						fail: (err) => {
							console.error('Failed to send form:', err);
						}
					});
				} else {
					this.connectWebSocket();
					this.websocket.onOpen(() => {
						this.websocket.send({
							data: JSON.stringify(cloneDialogue),
							success: () => {
								console.log('Form sent successfully after connection');
								// this.$nextTick(() => {
								// 	this.scrollChatToBottom();
								// });
							},
							fail: (err) => {
								console.error('Failed to send form after connection:', err);
							}
						});
					});
				}
			},

			setLLMmodel() {
				this.showModelPopup = true; // 点击设置按钮时，显示单选组件弹窗
				// this.getModelOptions(); // 调用接口获取单选选项数据
			},
			confirmModel() {
				this.llmModel = this.selectedModel; // 将选中的模型值赋给llmModel
				this.showModelPopup = false; // 隐藏单选组件弹窗
			},
			// setLLMmodel() {
			// 	this.showLlmConfig = true; // 点击设置按钮时，显示llm-config组件
			// },
			handleConfirm(modelValue) {
				this.llmModel = modelValue; // 获取llm-config组件传递过来的值，并赋值给当前页面的llmModel
				this.showLlmConfig = false; // 隐藏llm-config组件
			},
			// setLLMmodel() {
			// 	this.$refs['llm-config'].open(model => {
			// 		console.log('model', model);
			// 		this.llmModel = model
			// 	})
			// },

			// 更新最后一条消息
			updateLastMsg(param) {
				let length = this.msgList.length
				if (length === 0) {
					return
				}
				let lastMsg = this.msgList[length - 1]

				// 如果param是函数，则将最后一条消息作为参数传入该函数
				if (typeof param == 'function') {
					let callback = param;
					callback(lastMsg)
				} else {
					// 否则，将参数解构为data和cover两个变量
					const [data, cover = false] = arguments
					if (cover) {
						lastMsg = data
					} else {
						lastMsg = Object.assign(lastMsg, data)
					}
				}
				this.msgList.splice(length - 1, 1, lastMsg)
			},
			// 滚动窗口以显示最新的一条消息
			showLastMsg() {
				// 等待DOM更新
				this.$nextTick(() => {
					// 将scrollIntoView属性设置为"last-msg-item"，以便滚动窗口到最后一条消息
					this.scrollIntoView = "last-msg-item"
					// 等待DOM更新，即：滚动完成
					this.$nextTick(() => {
						// 将scrollIntoView属性设置为空，以便下次设置滚动条位置可被监听
						this.scrollIntoView = ""
					})
				})
			},
		}
	}
</script>

<style lang="scss">
	/* #ifndef APP-NVUE */
	page,
	/* #ifdef H5 */
	.container *,
	/* #endif */
	view,
	textarea,
	button {
		display: flex;
		box-sizing: border-box;
	}

	page {
		height: 100%;
		width: 100%;
	}

	/* #endif */

	.stop-responding {
		font-size: 14px;
		border-radius: 3px;
		margin-bottom: 15px;
		background-color: #f0b00a;
		color: #FFF;
		width: 90px;
		height: 30px;
		line-height: 30px;
		margin: 0 auto;
		justify-content: center;
		margin-bottom: 15px;
		/* #ifdef H5 */
		cursor: pointer;
		/* #endif */
	}

	.stop-responding:hover {
		box-shadow: 0 0 10px #aaa;
	}

	.container {
		height: 100%;
		background-color: #FAFAFA;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		// border: 1px solid blue;
	}

	.dialogue {
		display: flex;
		align-items: center;
		margin-bottom: 10px;
	}

	.bot-speak {
		flex-direction: row;
		background-color: #f8f8f8;
	}

	.bot-speak .message {
		background-color: #f8f8f8;
		/* 用户消息背景色为绿色 */
	}

	.user-speak {
		flex-direction: row-reverse;
	}

	.user-speak .message {
		background-color: #04BE02;
		/* 用户消息背景色为绿色 */
	}

	.avatar {
		width: 20px;
		height: 20px;
		border-radius: 50%;
		margin-right: 10px;
		margin-left: 10px;
	}

	.upload-button,
	.submit-button {
		margin: 10px;
		font-size: 14px;
		border-radius: 5px;
		width: 60px;
		height: 40px;
	}

	.upload-button {
		background-color: #ffffff;
		/* Default background color for upload button */
		border: 1px solid #ccc;
		/* Default border for upload button */
	}

	.upload-icon {
		width: 30px;
		height: 30px;
	}

	.submit-button {
		background-color: #ff5100;
		/* Color for submit button */
		border: none;
		/* No border for submit button */
		color: #ffffff;
		/* Text color for submit button */
	}

	/* Radio and Checkbox checked styles */
	.radio-checked,
	.checkbox-checked {
		color: #ff5100;
		/* Color for checked state */
	}

	radio:checked,
	checkbox:checked {
		background-color: #ff5100;
		border-color: #ff5100;
	}

	.message {
		max-width: 70%;
		background-color: #ffffff;
		/* 默认消息背景色为白色 */
		padding: 5px;
		border-radius: 5px;
		word-wrap: break-word;
		align-self: flex-start;
	}

	.model-popup {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background-color: rgba(0, 0, 0, 0.5);
		z-index: 999;
	}

	.popup-content {
		background-color: white;
		padding: 20px;
		border-radius: 10px;
		max-width: 300px;
		display: flex;
		flex-direction: column;
		justify-content: center;
		/* 使内部内容垂直居中 */
	}

	.option-item {
		display: flex;
		align-items: center;
		margin-bottom: 10px;
	}

	.option-text {
		margin-left: 10px;
	}

	.foot-box {
		width: 750rpx;
		display: flex;
		flex-direction: column;
		padding: 10px 0px;
		background-color: #FFF;
	}

	.foot-box-content {
		justify-content: space-around;
	}

	.textarea-box {
		padding: 8px 10px;
		background-color: #f9f9f9;
		border-radius: 5px;
	}

	.textarea-box .textarea {
		max-height: 120px;
		font-size: 14px;
		/* #ifndef APP-NVUE */
		overflow: auto;
		/* #endif */
		width: 450rpx;
		font-size: 14px;
	}

	/* #ifdef H5 */
	/*隐藏滚动条*/
	.textarea-box .textarea::-webkit-scrollbar {
		width: 0;
	}

	/* #endif */

	.input-placeholder {
		color: #bbb;
		line-height: 18px;
	}

	.trash,
	.send {
		width: 50px;
		height: 30px;
		justify-content: center;
		align-items: center;
		flex-shrink: 0;
	}

	.trash {
		width: 30rpx;
		margin-left: 10rpx;
	}

	.menu {
		justify-content: center;
		align-items: center;
		flex-shrink: 0;
	}

	.menu-item {
		width: 30rpx;
		margin: 0 10rpx;
	}

	.send {
		color: #FFF;
		border-radius: 4px;
		display: flex;
		margin: 0;
		padding: 0;
		font-size: 14px;
		margin-right: 20rpx;
	}

	/* #ifndef APP-NVUE */
	.send::after {
		display: none;
	}

	/* #endif */


	.msg-list {
		height: 0; //不可省略，先设置为0 再由flex: 1;撑开才是一个滚动容器
		flex: 1;
		width: 750rpx;
		// border: 1px solid red;
	}

	.noData {
		margin-top: 15px;
		text-align: center;
		width: 750rpx;
		color: #aaa;
		font-size: 12px;
		justify-content: center;
	}

	.open-ad-btn-box {
		justify-content: center;
		margin: 10px 0;
	}

	.tip-ai-ing {
		align-items: center;
		flex-direction: column;
		font-size: 14px;
		color: #919396;
		padding: 15px 0;
	}

	.uni-link {
		margin-left: 5px;
		line-height: 20px;
	}

	/* #ifdef H5 */
	@media screen and (min-width:650px) {
		.foot-box {
			border-top: solid 1px #dde0e2;
		}

		.container,
		.container * {
			max-width: 950px;
		}

		.container {
			box-shadow: 0 0 5px #e0e1e7;
			height: calc(100vh - 44px);
			margin: 22px auto;
			border-radius: 10px;
			overflow: hidden;
			background-color: #FAFAFA;
		}

		page {
			background-color: #efefef;
		}

		.container .header {
			height: 44px;
			line-height: 44px;
			border-bottom: 1px solid #F0F0F0;
			width: 100vw;
			justify-content: center;
			font-weight: 500;
		}

		.content {
			background-color: #f9f9f9;
			position: relative;
			max-width: 90%;
		}

		// .copy {
		// 	color: #888888;
		// 	position: absolute;
		// 	right: 8px;
		// 	top: 8px;
		// 	font-size: 12px;
		// 	cursor:pointer;
		// }
		// .copy :hover{
		// 	color: #4b9e5f;
		// }

		.foot-box,
		.foot-box-content,
		.msg-list,
		.msg-item,
		// .create_time,
		.noData,
		.textarea-box,
		.textarea,
		textarea-box {
			width: 100% !important;
		}

		.textarea-box,
		.textarea,
		textarea,
		textarea-box {
			height: 120px;
		}

		.foot-box,
		.textarea-box {
			background-color: #FFF;
		}

		.foot-box-content {
			flex-direction: column;
			justify-content: center;
			align-items: flex-end;
			padding-bottom: 0;
		}

		.pc-menu {
			padding: 0 10px;
		}

		.pc-menu-item {
			height: 20px;
			justify-content: center;
			align-items: center;
			align-content: center;
			display: flex;
			margin-right: 10px;
			cursor: pointer;
		}

		.pc-trash {
			opacity: 0.8;
		}

		.pc-trash image {
			height: 15px;
		}


		.textarea-box,
		.textarea-box * {
			// border: 1px solid #000;
		}

		.send-btn-box .send-btn-tip {
			color: #919396;
			margin-right: 8px;
			font-size: 12px;
			line-height: 28px;
		}
	}

	/* #endif */
	.retries-box {
		justify-content: center;
		align-items: center;
		font-size: 12px;
		color: #d2071b;
	}

	.retries-icon {
		margin-top: 1px;
		margin-left: 5px;
	}
</style>