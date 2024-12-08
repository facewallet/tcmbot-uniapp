<template>
	<view class="container" >
		<view class="header">
			<image src="/static/logo.png" class="logo" />
			<text class="title">中医机器人</text>
		</view>
		<scroll-view class="chat" ref="chat" scroll-y="true" :scroll-top="scrollTop" @scrolltolower="scrollChatToBottom">
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
		</scroll-view>
		<view class="input-box">
			<input type="text" placeholder="请输入消息" v-model="inputMessage" @keyup.enter="sendSocketMessage"
				class="input-message" />
			<button @click="sendSocketMessage"></button>
		</view>
	</view>
</template>
<style>
	.container {
		display: flex;
		flex-direction: column;
		height: 100vh;
		overflow: hidden;
	}

	.header {
		position: fixed;
		width: 100%;
		top: 0;
		left: 0;
		z-index: 1000;
		display: flex;
		align-items: center;
		justify-content: center;
		background-color: #f8f8f8;
		height: 40px;
	}

	.logo {
		width: 30px;
		height: 30px;
		margin-right: 10px;
	}

	.title {
		font-size: 18px;
	}

	.chat {
		flex: 1;
		margin-top: 10px;
		/* Adjusted to make space for the fixed header */
		overflow-y: auto;
		padding: 10px;
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

	.message {
		max-width: 70%;
		background-color: #ffffff;
		/* 默认消息背景色为白色 */
		padding: 5px;
		border-radius: 5px;
		word-wrap: break-word;
		align-self: flex-start;
	}

	.input-box {
		position: fixed;
		bottom: 0;
		left: 0;
		width: 100%;
		display: flex;
		align-items: center;
		padding: 10px;
		background-color: #f8f8f8;
	}

	.input-box input {
		flex: 1;
		border: 1px solid red;
		/* 输入框边框颜色改为红色 */
		border-radius: 5px;
		padding: 10px;
		margin-right: 10px;
		height: auto;
		min-height: 40px;
		max-height: 120px;
		overflow-y: auto;
		resize: none;
	}

	.input-box button {
		background-color: transparent;
		border: 0px;
		border-radius: 5px;
		padding: 10px;
		background-image: url('/static/send.png');
		background-size: cover;
		width: 30px;
		height: 30px;
		margin-right: 10px;
	}

	.input-box button:active {
		opacity: 0.8;
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
</style>



<script>
	export default {
		data() {
			return {
				dialogueList: [],
				inputMessage: '',
				websocket: null,
				websocketConnected: false,
				scrollTop: 0 // Add scrollTop to data
			};
		},
		methods: {
			scrollChatToBottom() {
				// this.scrollTop = 99999999; // Update scrollTop to scroll to the bottom
				this.scrollTop = this.$refs.chat.scrollHeight; // Update scrollTop to scroll to the bottom
				// let chat = this.$refs.chat;
				// if (chat) {
				// 	chat.scrollTop = chat.scrollHeight;
				// }
			},
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
						this.$nextTick(() => {
							this.scrollChatToBottom();
						});
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
			submitForm(dialogue) {
				uni.request({
					url: '/api/pub/dialogue',
					method: 'POST',
					data: dialogue,
					success: (res) => {
						console.log('Form submitted successfully:', res);
					},
					fail: (err) => {
						console.error('Form submission failed:', err);
					}
				});
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
							this.$nextTick(() => {
								this.scrollChatToBottom();
							});
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
								this.$nextTick(() => {
									this.scrollChatToBottom();
								});
							},
							fail: (err) => {
								console.error('Failed to send form after connection:', err);
							}
						});
					});
				}
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
			sendMessage() {
				// Implement sending message logic here
				// For example, add a new dialogue to the dialogueList
				this.dialogueList.push({
					speaker: 'user',
					type: 'text',
					content: this.inputMessage
				});
				this.inputMessage = '';
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
							this.$nextTick(() => {
								this.scrollChatToBottom();
							});
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
</script>