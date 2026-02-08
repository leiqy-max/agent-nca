<template>
  <div class="agent-wrapper" style="height: 100%; width: 100%;">
    <iframe :src="iframeSrc" style="width: 100%; height: 100%; border: none;"></iframe>
  </div>
</template>

<script>
export default {
  name: 'agent',
  data() {
    return {
      // Point to the React app (HashRouter version)
      // We append a timestamp to force reload if needed, though HashRouter usually handles itself
      iframeSrc: '/m/demo/agent-ui/'
    };
  },
  mounted() {
    // Optional: Pass token/user info to iframe via postMessage or localStorage if needed
    // For now, we assume simple public access or shared localStorage (same domain)
  }
}
</script>

<style scoped>
.agent-wrapper {
  overflow: hidden;
}
</style>