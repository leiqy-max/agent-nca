import os
import shutil
import time

def create_demo_structure(frontend_dist):
    print("Creating demo module structure...")
    # Target directory: demo/
    base_dir = "demo"
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir)
    
    # 1. Create agent-ui directory and copy React assets
    # React Base URL is /m/demo/agent-ui/
    agent_ui_dir = os.path.join(base_dir, "agent-ui")
    os.makedirs(agent_ui_dir)
    
    print(f"Copying React assets from {frontend_dist} to {agent_ui_dir}")
    if os.path.exists(frontend_dist):
        # Copy content of dist to agent-ui
        for item in os.listdir(frontend_dist):
            s = os.path.join(frontend_dist, item)
            d = os.path.join(agent_ui_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
    else:
        print(f"Error: {frontend_dist} does not exist. Please run 'npm run build' in frontend first.")
        return None

    # 2. Create views directory
    views_dir = os.path.join(base_dir, "views")
    os.makedirs(views_dir)
    
    build_time = str(int(time.time()))
    
    # 3. Create views-demo-agent.js (The Vue Wrapper)
    # This component wraps the iframe pointing to agent-ui
    views_content = """
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
"""
    with open(os.path.join(views_dir, "views-demo-agent.js"), "w") as f:
        f.write(views_content.strip())

    # 4. Create demo.js (The Module Entry Point)
    # Registers 'demo' module and routes
    demo_js_content = f"""
(function (global, factory) {{
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
    typeof define === 'function' && define.amd ? define(factory) :
    (global.m_demo = factory());
}}(this, function () {{
    console.log("[Demo Module] Initializing... Build Time: {build_time}");

    var chunkLoadingGlobal = window["webpackJsonp_demo"] = window["webpackJsonp_demo"] || [];
    var installedChunks = {{}};
    var modules = {{}};

    function webpackJsonpCallback(data) {{
        var chunkIds = data[0];
        var moreModules = data[1];
        var moduleId, chunkId, i = 0, resolves = [];
        
        for(moduleId in moreModules) {{
            if(Object.prototype.hasOwnProperty.call(moreModules, moduleId)) {{
                modules[moduleId] = moreModules[moduleId];
            }}
        }}

        for(i = 0; i < chunkIds.length; i++) {{
            chunkId = chunkIds[i];
            if(Object.prototype.hasOwnProperty.call(installedChunks, chunkId) && installedChunks[chunkId]) {{
                resolves.push(installedChunks[chunkId][0]);
            }}
            installedChunks[chunkId] = 0; 
        }}
        
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
            console.error("[Demo Module] Module not found:", moduleId, "Available:", Object.keys(modules));
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
        console.log("[Demo Module] Factory called. PublicPath:", publicPath);
        
        return {{
            router: function(menusRouter, moduleName) {{
                console.log("[Demo Module] Router processing", menusRouter.length, "routes. ModuleName:", moduleName);
                
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
                        console.log("[Demo Module] Loading component for:", item.path);
                        return new Promise(function(resolve, reject) {{
                            if(modules["demo/views/agent"]) {{
                                resolve(__webpack_require__("demo/views/agent"));
                                return;
                            }}
                            
                            var resolveWrapper = function() {{
                                try {{
                                    var component = __webpack_require__("demo/views/agent");
                                    resolve(component);
                                }} catch(e) {{
                                    reject(e);
                                }}
                            }};

                            installedChunks["demo/views/agent"] = [resolveWrapper, reject];
                            
                            var script = document.createElement('script');
                            // Ensure this path matches Nginx location
                            script.src = '/m/demo/views/views-demo-agent.js?v={build_time}';
                            script.onerror = function(e) {{
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
    with open(os.path.join(base_dir, "demo.js"), "w") as f:
        f.write(demo_js_content.strip())
    
    return base_dir

def zip_demo(demo_dir):
    print("Zipping demo package...")
    # Zip the demo directory itself
    # If we want demo.zip to contain 'demo' folder at root
    shutil.make_archive("demo", "zip", root_dir=os.getcwd(), base_dir="demo")
    print("Created demo.zip")

if __name__ == "__main__":
    frontend_dist = os.path.join(os.getcwd(), "frontend", "dist")
    demo_dir = create_demo_structure(frontend_dist)
    if demo_dir:
        zip_demo(demo_dir)
