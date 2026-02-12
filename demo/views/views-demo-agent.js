(window["webpackJsonp_demo"] = window["webpackJsonp_demo"] || []).push([
  ["demo/views/agent"],
  {
    "demo/views/agent": function (module, exports, __webpack_require__) {
      "use strict";
      console.log("[DemoAgent] Module Loaded Successfully!"); 
      var component = {
        name: "DemoAgentWrapper",
        data: function () {
          return { 
            iframeSrc: "" 
          }
        },
        mounted: function() {
            console.log("[DemoAgent] Component Mounted");
            this.initIframe();
        },
        watch: {
            '$route': 'initIframe'
        },
        methods: {
            initIframe: function() {
                var baseUrl = "/m/demo/agent-ui/";
                var query = [];
                
                if (this.$route.meta && this.$route.meta.inputParams) {
                    var p = this.$route.meta.inputParams;
                    if(p.userId) query.push("userId=" + encodeURIComponent(p.userId));
                    if(p.tenantId) query.push("tenantId=" + encodeURIComponent(p.tenantId));
                }
                
                var token = localStorage.getItem('access_token') || localStorage.getItem('token');
                if (window.nc && window.nc.token) token = window.nc.token;
                if (token) query.push("token=" + encodeURIComponent(token));
                
                if (window.location.search) {
                    var search = window.location.search.substring(1);
                    if (search) query.push(search);
                }
                
                var queryString = query.length ? "?" + query.join("&") : "";
                this.iframeSrc = baseUrl + queryString;
                console.log("[DemoAgent] Loading Iframe:", this.iframeSrc);
            }
        },
        render: function (h) {
          return h(
            "div",
            { style: { height: "100%", width: "100%", overflow: "hidden" } },
            [
              this.iframeSrc ? h("iframe", {
                attrs: { src: this.iframeSrc, frameborder: "0" },
                style: { width: "100%", height: "100%", border: "none" }
              }) : h("div", "Loading...")
            ]
          )
        }
      }
      module.exports = component
      module.exports.default = component
      module.exports.__esModule = true
    }
  }
]);