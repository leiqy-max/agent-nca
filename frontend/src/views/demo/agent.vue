<template>
  <div style="height: 100%; width: 100%;">
    <iframe v-if="iframeSrc" :src="iframeSrc" frameborder="0" style="width: 100%; height: 100%;"></iframe>
    <div v-else>正在初始化智能助手...</div>
  </div>
</template>

<script>
export default {
  name: "AgentWrapper",
  data() {
    return {
      iframeSrc: "",
    };
  },
  mounted() {
    this.initIframe();
  },
  methods: {
    initIframe() {
      const baseUrl = "/m/demo/agent-ui/";
      let username = "";
      try {
        const topDoc = window.top.document;
        const selectors = [".el-dropdown-link", ".user-name", ".username", ".top-user-name"];
        for (const selector of selectors) {
          const el = topDoc.querySelector(selector);
          if (el && el.textContent.trim()) {
            username = el.textContent.trim();
            console.log(`[AgentWrapper] Detected username: ${username}`);
            break;
          }
        }
      } catch (e) {
        console.error("[AgentWrapper] Failed to access parent window for SSO:", e);
      }
      
      const url = new URL(baseUrl, window.location.origin);
      if (username) {
        url.searchParams.append("username", username);
      }
      
      this.iframeSrc = url.href;
      console.log(`[AgentWrapper] Loading iframe with src: ${this.iframeSrc}`);
    },
  },
};
</script>

<style scoped>
/* Add any specific styles for the wrapper here */
</style>
