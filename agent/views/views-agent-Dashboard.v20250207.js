(window["webpackJsonp_agent"] = window["webpackJsonp_agent"] || []).push([
    ["agent/views/views-agent-Dashboard"], // Chunk ID
    {
        // Module definitions
        "./views/agent/index.vue": function(module, exports) {
            console.log("[Agent Chunk] Initializing Dashboard Component (v20250207)");
            var component = {
                name: "AgentDashboard",
                data: function() {
                    return {
                        currentDate: new Date().toLocaleDateString(),
                        projectName: "zz-agent-out-develop",
                        projectDesc: "智能问答助手项目 (Agent) - Loaded via strict structure (v2)",
                        loadTime: new Date().toISOString()
                    };
                },
                render: function(h) {
                    var _vm = this;
                    return h("div", { staticStyle: { padding: "24px", background: "#f0f2f5", minHeight: "100%" } }, [
                        h("div", { staticStyle: { background: "#fff", padding: "24px", borderRadius: "8px", boxShadow: "0 1px 2px rgba(0,0,0,0.1)" } }, [
                            h("h2", { staticStyle: { margin: "0 0 16px 0", borderBottom: "1px solid #eee", paddingBottom: "12px" } }, [
                                _vm._v("🚀 Agent Dashboard (v2)")
                            ]),
                            h("div", { staticStyle: { display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "16px" } }, [
                                h("div", [
                                    h("strong", "项目名称: "), _vm._v(_vm.projectName)
                                ]),
                                h("div", [
                                    h("strong", "模块来源: "), _vm._v("views/views-agent-Dashboard.v20250207.js")
                                ])
                            ])
                        ])
                    ]);
                }
            };
            module.exports = component;
            module.exports.default = component;
            module.exports.__esModule = true;
        }
    }
]);
