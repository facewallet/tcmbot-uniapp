<template>
	<view class="container">
		<!-- #ifdef H5 -->
		<view v-if="isWidescreen" class="header">中医机器人Web版中医机器人Web版中医机器人Web版中医机器人Web版</view>
		<!-- #endif -->
		<scroll-view :scroll-into-view="scrollIntoView" scroll-y="true" class="msg-list" :enable-flex="true">
			<view v-for="(dialogue, index) in dialogueList" :key="index" class="dialogue"
				:class="{ 'bot-speak': dialogue.speaker === 'bot', 'user-speak': dialogue.speaker === 'user' }">
				
				<uni-icons v-if="dialogue.speaker === 'bot'" color="#ff5100" type="headphones" size="30"></uni-icons>
				<uni-icons v-else color="#ff5100" type="contact" size="30"></uni-icons>
				<view class="message" :style="{ backgroundColor: dialogue.speaker === 'user'? '#ffffff' : '#f8f8f8' }">
					<view v-if="dialogue.channel_label && dialogue.speaker ==='bot'" style="margin-top: 5px;">来自：{{ dialogue.channel_label }}</view>
					<view v-if="dialogue.channel_label && dialogue.speaker ==='user'" style="margin-top: 5px;">发往：{{ dialogue.channel_label }}</view>
					<view v-if="dialogue.type === 'text'" style="margin-top: 5px;" v-html="dialogue.content"></view>
					<form style="margin-top: 5px;" v-if="dialogue.type === 'form'" @submit="submitSocketForm(dialogue)">
						<view v-for="formItem in dialogue.forms" :key="formItem.id" style="flex-direction: column;">
							<label>{{formItem.label}}</label>
							<input v-if="formItem.type === 'text' || formItem.type === 'password'" :type="formItem.type"
								:placeholder="formItem.placeholder" v-model="formItem.value"
								:required="formItem.required === 'true'" />
							<radio-group style="flex-direction: column;" v-if="formItem.type === 'radio'"
								@change="radioGroupChange($event,formItem)">
								<label v-for="option in formItem.options" :key="option.id" class="radio-label">
									<radio :value="option.value" :checked="formItem.value === option.value" />
									{{ option.label }}
								</label>
							</radio-group>
							<checkbox-group v-if="formItem.type === 'checkbox'">
								<label v-for="option in formItem.options" :key="option.id">
									<checkbox :value="option.value"
										:checked="formItem.values && formItem.values.includes(option.value)"
										@change="checkboxChange(formItem, option.value)" />
									{{ option.label }}
								</label>
							</checkbox-group>
							<button v-if="formItem.type === 'file'" @click="uploadFile" class="upload-button">
								<!-- <image src="/static/upload.png" class="upload-icon" /> -->
							</button>
						</view>
						<button form-type="submit" :disabled="!isLastBotForm(dialogue)" class="submit-button">提交</button>
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
					<uni-icons class="menu-item" @click="setLLMmodel" color="#ff5100" size="20px"
						type="bars"></uni-icons>
				</view>
				<view class="textarea-box">
					<textarea v-model="inputMessage" :cursor-spacing="15" class="textarea" :auto-height="!isWidescreen"
						placeholder="请输入要发给中医机器人的内容" :maxlength="-1" :adjust-position="false"
						:disable-default-padding="false" placeholder-class="input-placeholder"></textarea>
				</view>
				<view class="send-btn-box" :title="(msgList.length && msgList.length%2!== 0)? 'ai正在回复中不能发送':''">
					<!-- #ifdef H5 -->
					<text v-if="isWidescreen" class="send-btn-tip">↵ 发送 / shift + ↵ 换行</text>
					<!-- #endif -->
					<!-- <button @click="sendSocketMessage" class="send" type="primary">发送</button> -->
					<uni-icons @click="sendSocketMessage" class="send" color="#ff5100" type="paperplane-filled" size="30"></uni-icons>

				</view>
			</view>
		</view>
		<view class="model-popup" v-if="showModelPopup">
			<view class="popup-content">
				<radio-group  class="radio-group" @change="radioChange">
					<view class="option-item" v-for="(option, index) in modelOptions" :key="index">
						<!-- <radio :value="option.value" /> -->
						<radio :value="option.value" :disabled="option.disabled === 'YES'" :checked="option.value === this.llmModel" />
						<text class="option-text">{{ option.name }}</text>
					</view>
				</radio-group>
				<button @click="confirmModel" class="submit-button">确定</button>
			</view>
		</view>
		<view v-if="isWidescreen">
		  <a href="https://beian.miit.gov.cn/" style="font-size: 12px; text-decoration: none;">备案号：京ICP备20000763号</a>
		</view>

	</view>
</template>


<script>
	// 键盘的shift键是否被按下
	let shiftKeyPressed = false

	export default {
		data() {
			return {
				uuid:'',
				host:'localhost:8086',
				apiBaseUrl : 'https://m.tcmbot.com',
				socketBaseUrl : 'wss://m.tcmbot.com',
				trace_id:'',
				dialogueList: [],
				agent_dialogueList: [],
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

				keyboardHeight: 0,
				showLlmConfig: false, // 控制llm-config组件是否显示，初始为隐藏
				llmModel: 'tcm-all',
				showModelPopup: false, // 控制单选组件弹窗是否显示，初始为隐藏
				modelOptions: [{
					name: '全部模型',
					value: 'tcm-all',checked: true,disabled: false
				}, {
					name: '中医大模型',
					value: 'tcm-rag',checked: false,disabled: false
				},
				{
					name: '中医小模型',
					value: 'tcm-ner',checked: false,disabled: false
				},
				{
					name: '中医知识图谱',
					value: 'tcm-graphrag',checked: false,disabled: false
				},
				{
					name: '中医智能体',
					value: 'tcm-agent',checked: false,disabled: true
				},{
					name: '中医介子推',
					value: 'tcm-jzt',checked: false,disabled: true
				},
				
				], // 存储从接口获取的单选选项数据，格式如 [{name: '选项1', value: 'option1'},...]
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
			const systemInfo = uni.getSystemInfoSync();
			console.log('-----------------');
			console.log(systemInfo);
			if (systemInfo.platform === 'web') {
			  this.apiBaseUrl = 'https://www.tcmbot.com';
			  this.socketBaseUrl = 'wss://www.tcmbot.com';
			} else {
			  this.apiBaseUrl = 'https://m.tcmbot.com';
			  this.socketBaseUrl = 'wss://m.tcmbot.com';
			}
			this.fetchWelcome();
			this.fetchChannel();
			this.connectWebSocket();
			this.uuid = this.generateUUID();
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
						// setTimeout(() => {
						// 	this.beforeSend();
						// }, 300)
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
					url: this.socketBaseUrl+'/api/socket/dialogue',
					// url: 'ws://localhost:8086/api/socket/dialogue',
					success: () => {
						console.log('WebSocket connected');
					}
				});

				this.websocket.onOpen(() => {
					this.websocketConnected = true;
				});

				this.websocket.onMessage((message) => {
					if(this.trace_id ===''){
						uni.hideLoading();
					}
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
							console.log("data.dialogue")
							console.log(data.dialogue)
							this.dialogueList.push(data.dialogue);
							if(data.dialogue.trace_id === this.trace_id){
								uni.hideLoading();
							}
							if(data.dialogue.channel_name ==='tcm-agent'){
								this.agent_dialogueList.push(data.dialogue);
							}
						}
						if (data.dialogueList) {
							for (let i = 0; i < data.dialogueList.length; i++) {
								const dialogue = data.dialogueList[i];
								this.dialogueList.push(dialogue);
								if(dialogue.trace_id === this.trace_id){
									uni.hideLoading();
								}
								if(dialogue.channel_name ==='tcm-agent'){
									this.agent_dialogueList.push(dialogue);
								}
							}
							// this.dialogueList.push(...data.dialogueList);
						}
						this.showLastMsg()
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
				this.trace_id = this.generateUUID();
				const message = {
					speaker: 'user',
					type: 'text',
					content: this.inputMessage,
					user_intent: 'user_ask',
					uuid:this.uuid,
					trace_id: this.trace_id,
					channel_name: this.llmModel
					// timestamp: new Date().getTime()
				};
				console.log(message)
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
				uni.showLoading({title:'思考中'})
				setTimeout(function(){
					uni.hideLoading();
				},10000);
			},

			fetchWelcome() {
				uni.request({
					url: this.apiBaseUrl+'/api/pub/dialogue/welcome',
					// url: 'http://localhost:8086/api/pub/dialogue/welcome',
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
							// this.showLastMsg();
						}
					},
					fail: (err) => {
						console.error(err);
					}
				});
			},
			fetchChannel() {
				uni.request({
					url: this.apiBaseUrl+'/api/pub/dialogue/channel',
					// url: 'http://localhost:8086/api/pub/dialogue/channel',
					success: (res) => {
						console.log(res)
						if (res.data.meta.code === 0) {
							const data = res.data.data;
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
				this.trace_id = this.generateUUID();
				cloneDialogue.trace_id = this.trace_id;
				this.dialogueList.push(cloneDialogue);
				if (this.websocketConnected) {
					this.websocket.send({
						data: JSON.stringify(cloneDialogue),
						success: () => {
							console.log('Form sent successfully');
							this.showLastMsg();
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
								this.showLastMsg();
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
				uni.showLoading({title:'思考中'})
			},

			setLLMmodel() {
				this.showModelPopup = true; // 点击设置按钮时，显示单选组件弹窗
				
			},
			confirmModel() {
				console.log('Selected llmModel:', this.llmModel);
				this.showModelPopup = false; // 隐藏单选组件弹窗
			},
			generateUUID() {
			          const timestamp = Date.now().toString(16); // 获取当前时间戳并转换为十六进制
			          const randomPart = Math.floor(Math.random() * 0x100000000).toString(16).padStart(8, '0'); // 生成随机数并转换为十六进制，不足8位补0
			          return `${timestamp}-${randomPart}`;
			      },
			radioChange(e) {
				// 当radio选项变化时，更新selectedModel的值
				// this.selectedModel = e.detail.value;
				this.llmModel = e.detail.value;
			},
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
			isLastBotForm(dialogue){
				const lastDialogue = this.agent_dialogueList[this.agent_dialogueList.length - 1];
				return dialogue === lastDialogue && lastDialogue.type === 'form';
				// return lastDialogue.type === 'form';
			},
			
		}
	}
</script>

<style>
	/* #ifndef APP-NVGE */
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
		position: relative;
		/* 给父容器设置相对定位，作为model-popup定位的参照 */
	}

	.dialogue {
		display: flex;
		align-items: center;
		margin-bottom: 5px;
		margin-left: 10px;
		margin-right:10px;
		/* margin-top:10px; */
	}

	.bot-speak {
		flex-direction: row;
		background-color: #f8f8f8;
	}

	.bot-speak.message {
		background-color: #f8f8f8;
		flex-direction: column;
	}

	.user-speak {
		flex-direction: row-reverse;
	}

	.user-speak.message {
		background-color: #04BE02;
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
		font-size: 14px;
		border-radius: 5px;
		background-color: #ff5100;
		width: 60px;
		height: 40px;
		border: none;
		color: #ffffff;
		display: flex;
		/* 设置为flex布局，方便内部元素的对齐操作 */
		justify-content: center;
		/* 水平方向居中 */
		align-items: center;
		/* 垂直方向居中 */
	}

	.upload-button {
		background-color: #ffffff;
		border: 1px solid #ccc;
	}

	.upload-icon {
		width: 30px;
		height: 30px;
	}

	.message {
		max-width: 70%;
		background-color: #ffffff;
		padding: 5px;
		border-radius: 5px;
		word-wrap: break-word;
		align-self: flex-start;
		flex-direction: column;
	}

	.radio-group,
	.checkbox-group {
		display: flex;
		flex-wrap: wrap;
	}

	.radio-label,
	.checkbox-label {
		display: flex;
		align-items: center;
		margin: 5px;
	}

	.radio-input,
	.checkbox-input {
		margin-right: 5px;
	}

	.radio-text,
	.checkbox-text {
		margin-left: 5px;
	}

	.radio-group {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		/* 让选项左对齐，更符合常规布局习惯 */
	}

	.radio-label {
		display: flex;
		align-items: center;
		/* 让单选按钮和文字垂直居中对齐 */
		margin-bottom: 10px;
		/* 每个选项之间添加一定间距，增强可读性 */
	}

	/* 手机端model-popup样式 */
	.model-popup {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		display: flex;
		justify-content: center;
		align-items: center;
		background-color: rgba(0, 0, 0, 0.5);
		z-index: 999;
	}
	.popup-content {
		background-color: white;
		padding: 20px;
		border-radius: 10px;
		width: 80%;
		flex-direction: column;
		/* 让内容区域占弹窗宽度的一定比例，更美观 */
	}

	/* PC端model-popup样式，通过条件编译适配 */
	/* #ifdef H5 */
	.model-popup {
		position: fixed;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 400px;
		/* 可以根据PC端实际情况调整合适的宽度 */
		height: 300px;
		/* 可以根据PC端实际情况调整合适的高度 */
		background-color: rgba(0, 0, 0, 0.5);
		display: flex;
		justify-content: center;
		align-items: center;
		z-index: 999;
		box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
		/* 添加阴影效果，增强弹窗立体感 */
	}

	.popup-content {
		background-color: white;
		padding: 20px;
		border-radius: 10px;
		width: 80%;
		flex-direction: column;
		/* 让内容区域占弹窗宽度的一定比例，更美观 */
	}

	/* #endif */
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
		border: 1px solid #ff5100;
		border-radius: 5px;
	}

	.textarea-box.textarea {
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
	.textarea-box.textarea::-webkit-scrollbar {
		width: 0;
	}

	/* #endif */

	.input-placeholder {
		color: #bbb;
		line-height: 18px;
	}

	.trash,
	.send {
		color: #ff5100;
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
		height: 0;
		flex: 1;
		width: 750rpx;
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

		.container.header {
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

		.foot-box,
		.foot-box-content,
		.msg-list,
		.msg-item,
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
		.textarea-box * {}

		.send-btn-box.send-btn-tip {
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