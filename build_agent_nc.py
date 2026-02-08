import os
import shutil
import time
import json

def create_agent_structure(dist_path):
    print("Creating agent module structure...")
    agent_dir = os.path.join(os.getcwd(), "agent")
    if os.path.exists(agent_dir):
        shutil.rmtree(agent_dir)
    os.makedirs(agent_dir)
    
    # 1. Copy React app assets to root of agent/
    print(f"Copying assets from {dist_path} to {agent_dir}")
    if os.path.exists(dist_path):
        for item in os.listdir(dist_path):
            s = os.path.join(dist_path, item)
            d = os.path.join(agent_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
    else:
        print(f"Warning: {dist_path} does not exist. Skipping asset copy.")

    # 2. Create views directory
    views_dir = os.path.join(agent_dir, "views")
    os.makedirs(views_dir)
    
    # 3. Create views-agent-index.js (The Vue Wrapper)
    views_content = """
(window["webpackJsonp_agent"] = window["webpackJsonp_agent"] || []).push([
  ["agent/views/index"],
  {
    "agent/views/index": function (module, exports, __webpack_require__) {
      "use strict";
      console.log("[AgentWrapper] Module Loaded Successfully!"); 
      var component = {
        name: "AgentWrapper",
        data: function () {
          return { 
            iframeSrc: "" 
          }
        },
        mounted: function() {
            console.log("[AgentWrapper] Component Mounted");
            this.initIframe();
        },
        watch: {
            '$route': 'initIframe'
        },
        methods: {
            initIframe: function() {
                var baseUrl = "/m/agent/";
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
                console.log("[AgentWrapper] Loading Iframe:", this.iframeSrc);
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
"""
    with open(os.path.join(views_dir, "views-agent-index.js"), "w") as f:
        f.write(views_content.strip())

    # 4. Create agent.js (The Module Entry Point)
    build_time = str(int(time.time()))
    agent_js_content = f"""
(function (global, factory) {{
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
    typeof define === 'function' && define.amd ? define(factory) :
    (global.m_agent = factory());
}}(this, function () {{
    console.log("[Agent Module] Initializing... Build Time: {build_time} (FIXED VERSION)");

    var chunkLoadingGlobal = window["webpackJsonp_agent"] = window["webpackJsonp_agent"] || [];
    var installedChunks = {{}};
    var modules = {{}};

    function webpackJsonpCallback(data) {{
        var chunkIds = data[0];
        var moreModules = data[1];
        var moduleId, chunkId, i = 0, resolves = [];
        
        // 1. Register modules first
        for(moduleId in moreModules) {{
            if(Object.prototype.hasOwnProperty.call(moreModules, moduleId)) {{
                modules[moduleId] = moreModules[moduleId];
            }}
        }}

        // 2. Resolve chunks
        for(i = 0; i < chunkIds.length; i++) {{
            chunkId = chunkIds[i];
            if(Object.prototype.hasOwnProperty.call(installedChunks, chunkId) && installedChunks[chunkId]) {{
                resolves.push(installedChunks[chunkId][0]);
            }}
            installedChunks[chunkId] = 0; 
        }}
        
        // 3. Execute callbacks
        while(resolves.length) {{
            resolves.shift()();
        }}
    }};

    var existingPush = chunkLoadingGlobal.push;
    chunkLoadingGlobal.push = webpackJsonpCallback;
    var copy = chunkLoadingGlobal.slice();
    for(var i=0; i<copy.length; i++) {{
        webpackJsonpCallback(copy[i]);
    }}

    function __webpack_require__(moduleId) {{
        var module = {{ exports: {{}} }};
        if(modules[moduleId]) {{
            modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
        }} else {{
            console.error("[Agent Module] Module not found:", moduleId, "Available:", Object.keys(modules));
        }}
        return module.exports;
    }};

    function getUrlParams(paramStr) {{
        var paramsObj = {{}};
        if (paramStr && paramStr.indexOf("?") != -1) {{
            var str = paramStr.split("?")[1];
            var paramArr = str.split("&");
            for(var i = 0; i < paramArr.length; i ++) {{
                if(paramArr[i].indexOf("=") != -1) {{
                    paramsObj[paramArr[i].split("=")[0]] = unescape(paramArr[i].split("=")[1]);
                }}
            }}
        }}
        return paramsObj;
    }}

    return function(publicPath) {{
        console.log("[Agent Module] Factory called. PublicPath:", publicPath);
        
        return {{
            router: function(menusRouter, moduleName) {{
                console.log("[Agent Module] Router processing", menusRouter.length, "routes. ModuleName:", moduleName);
                
                return menusRouter.map(function(item) {{
                    var props = {{}};
                    var route = {{
                        name: item.label,
                        path: item.path,
                        props: props,
                        query: {{}} ,
                        meta: {{
                            keepAlive: Number(item['keepAlive']) === 1,
                            moduleName: moduleName,
                            name: item.label,
                            resource: item.resource || [],
                            defaultParams: {{ grayMode: "" }},
                            inputParams: {{ userId: "", tenantId: "" }}
                        }}
                    }};

                    if (typeof nc !== 'undefined' && nc.util && nc.util.getStore) {{
                        var userInfo = nc.util.getStore({{name:"userInfo"}});
                        if (userInfo) {{
                            route.meta.inputParams.userId = userInfo.id;
                            route.meta.inputParams.tenantId = userInfo.tenantId;
                        }}
                    }}

                    var realPath = item.path;
                    if (realPath.indexOf('/' + moduleName) === 0) {{
                        realPath = realPath.replace('/' + moduleName, '');
                    }}
                    
                    var params = getUrlParams(item.path);
                    if(params) {{
                        route.props = params;
                        Object.assign(route.meta.inputParams, params);
                    }}

                    route.component = function() {{
                        console.log("[Agent Module] Loading component for:", item.path);
                        return new Promise(function(resolve, reject) {{
                            if(modules["agent/views/index"]) {{
                                console.log("[Agent Module] Component already loaded. Returning directly.");
                                resolve(__webpack_require__("agent/views/index"));
                                return;
                            }}
                            
                            // Define callback wrapper that actually requires the module
                            var resolveWrapper = function() {{
                                try {{
                                    console.log("[Agent Module] Async resolving component...");
                                    var component = __webpack_require__("agent/views/index");
                                    console.log("[Agent Module] Component required:", component);
                                    resolve(component);
                                }} catch(e) {{
                                    console.error("[Agent Module] Require failed in async callback", e);
                                    reject(e);
                                }}
                            }};

                            installedChunks["agent/views/index"] = [resolveWrapper, reject];
                            
                            var script = document.createElement('script');
                            script.src = '/m/agent/views/views-agent-index.js?v={build_time}';
                            script.onerror = function(e) {{
                                console.error("[Agent Module] Script load error", e);
                                reject(e);
                            }};
                            document.head.appendChild(script);
                        }});
                    }};

                    return route;
                }});
            }},
            store: {{}}
        }};
    }};
}}));
"""
    with open(os.path.join(agent_dir, "agent.js"), "w") as f:
        f.write(agent_js_content.strip())
    
    return agent_dir

def zip_agent(agent_dir):
    print("Zipping agent package...")
    shutil.make_archive("agent", "zip", root_dir=os.getcwd(), base_dir="agent")
    print("Created agent.zip")

if __name__ == "__main__":
    dist_path = os.path.join(os.getcwd(), "frontend", "dist")
    agent_dir = create_agent_structure(dist_path)
    zip_agent(agent_dir)
