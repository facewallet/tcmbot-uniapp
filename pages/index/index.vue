<template>
    <view>
        <button @click="sendMessage">发送消息</button>
    </view>
</template>

<script>
export default {
    data() {
        return {
            websocket: null
        }
    },
    onShow() {
        this.connectWebSocket();
    },
    methods: {
        connectWebSocket() {
            this.websocket = uni.connectSocket({
                url: 'ws://localhost:8086/api/socket/dialogue',
                success() {
                    console.log('WebSocket连接成功');
                }
            });

            this.websocket.onOpen(() => {
                console.log('WebSocket连接已打开');
            });

            this.websocket.onMessage((message) => {
                console.log('收到服务器内容：' + message.data);
            });

            this.websocket.onError((error) => {
                console.log('WebSocket连接打开失败，请检查！', error);
            });

            this.websocket.onClose(() => {
                console.log('WebSocket 已关闭！');
            });
        },
        sendMessage() {
			const dialogue = {
				"speaker": "user",
				"type": "text",
				"content": "你的消息"
			}
            this.websocket.send({
                data: JSON.stringify(dialogue),
                success() {
                    console.log('消息发送成功');
                }
			})

        }
    }
}
</script>
