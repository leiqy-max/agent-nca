<template>
  <div class="chat-container">
    <div class="messages" ref="messagesContainer">
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.type]">
        <div class="avatar">{{ msg.type === 'user' ? 'U' : 'AI' }}</div>
        <div class="content">
          <div v-if="msg.text" v-html="formatText(msg.text)"></div>
          <div v-if="msg.sources && msg.sources.length" class="sources">
            <div class="source-title">参考文档:</div>
            <div v-for="(source, sIndex) in msg.sources" :key="sIndex" class="source-item">
              <a href="#" @click.prevent="downloadSource(source.id)">{{ source.filename }}</a>
            </div>
          </div>
        </div>
      </div>
      <div v-if="loading" class="message ai">
        <div class="avatar">AI</div>
        <div class="content">思考中...</div>
      </div>
    </div>
    <div class="input-area">
      <input 
        v-model="input" 
        @keyup.enter="sendMessage" 
        placeholder="请输入您的问题..." 
        :disabled="loading"
      />
      <button @click="sendMessage" :disabled="loading || !input.trim()">发送</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      input: '',
      messages: [],
      loading: false
    };
  },
  methods: {
    formatText(text) {
      // Simple newline to br
      return text.replace(/\n/g, '<br>');
    },
    async sendMessage() {
      if (!this.input.trim()) return;
      
      const question = this.input;
      this.messages.push({ type: 'user', text: question });
      this.input = '';
      this.loading = true;
      
      try {
        // Direct call to agent-api (proxied by Nginx)
        // Note: We bypass nc.rapi because this is a custom external service, not a standard NC service
        const res = await axios.post('/agent-api/get_answer', {
          question: question
        });
        
        const data = res.data;
        this.messages.push({
          type: 'ai',
          text: data.answer,
          sources: data.sources
        });
      } catch (e) {
        this.messages.push({ type: 'ai', text: '抱歉，请求出错: ' + e.message });
      } finally {
        this.loading = false;
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      }
    },
    downloadSource(id) {
        window.open(`/agent-api/download_source/${id}`, '_blank');
    },
    scrollToBottom() {
      const el = this.$refs.messagesContainer;
      if (el) el.scrollTop = el.scrollHeight;
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fa;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.message {
  display: flex;
  margin-bottom: 20px;
}
.message.user {
  flex-direction: row-reverse;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #ccc;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin: 0 10px;
}
.message.ai .avatar {
  background: #409EFF;
}
.message.user .avatar {
  background: #67C23A;
}
.content {
  background: #fff;
  padding: 10px 15px;
  border-radius: 5px;
  max-width: 70%;
  line-height: 1.5;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.message.user .content {
  background: #95ec69;
}
.sources {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #eee;
  font-size: 12px;
}
.source-title {
  color: #999;
  margin-bottom: 5px;
}
.input-area {
  padding: 20px;
  background: #fff;
  border-top: 1px solid #eee;
  display: flex;
}
.input-area input {
  flex: 1;
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  margin-right: 10px;
  outline: none;
}
.input-area button {
  padding: 10px 20px;
  background: #409EFF;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.input-area button:disabled {
  background: #a0cfff;
  cursor: not-allowed;
}
</style>