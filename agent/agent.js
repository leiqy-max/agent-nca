(function(global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
    typeof define === 'function' && define.amd ? define(factory) :
    (global.m_agent = factory());
}(this, function() {
    console.log("[Agent Module] Initializing Strict Mode (v20250207)...");

    // =========================================================================
    // Webpack Runtime
    // =========================================================================
    var modules = {};
    var installedChunks = { "agent/agent": 0 };

    function __webpack_require__(moduleId) {
        if (modules[moduleId]) {
            return modules[moduleId].exports;
        }
        var module = modules[moduleId] = {
            i: moduleId,
            l: false,
            exports: {}
        };
        if (typeof modules[moduleId] === 'function') {
             modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
        } else {
             return modules[moduleId];
        }
        module.l = true;
        return module.exports;
    }

    __webpack_require__.m = modules;
    __webpack_require__.c = modules; 

    // jsonpScriptSrc
    function jsonpScriptSrc(chunkId) {
        var publicPath = window.__agent_base_path__ || "/m/agent/";
        // Fix for double slash if publicPath ends with / and src starts with /
        if (publicPath.slice(-1) !== '/') publicPath += '/';
        
        var src = ({
            "agent/views/views-agent-Dashboard": "views/views-agent-Dashboard"
        }[chunkId] || chunkId) + "." + ({
            "agent/views/views-agent-Dashboard": "v20250207"
        }[chunkId] || "hash") + ".js";
        
        return publicPath + src;
    }

    // __webpack_require__.e
    __webpack_require__.e = function(chunkId) {
        var promises = [];
        var installedChunkData = installedChunks[chunkId];
        if (installedChunkData !== 0) {
            if (installedChunkData) {
                promises.push(installedChunkData[2]);
            } else {
                var promise = new Promise(function(resolve, reject) {
                    installedChunkData = installedChunks[chunkId] = [resolve, reject];
                });
                promises.push(installedChunkData[2] = promise);

                var script = document.createElement('script');
                script.charset = 'utf-8';
                script.timeout = 120;
                script.src = jsonpScriptSrc(chunkId);
                
                var onScriptComplete = function(event) {
                    script.onerror = script.onload = null;
                    clearTimeout(timeout);
                    var chunk = installedChunks[chunkId];
                    if (chunk !== 0) {
                        if (chunk) {
                            var errorType = event && (event.type === 'load' ? 'missing' : event.type);
                            var realSrc = event && event.target && event.target.src;
                            var error = new Error('Loading chunk ' + chunkId + ' failed.\n(' + errorType + ': ' + realSrc + ')');
                            error.type = errorType;
                            error.request = realSrc;
                            chunk[1](error);
                        }
                        installedChunks[chunkId] = undefined;
                    }
                };
                var timeout = setTimeout(function() {
                    onScriptComplete({ type: 'timeout', target: script });
                }, 120000);
                script.onerror = script.onload = onScriptComplete;
                document.head.appendChild(script);
            }
        }
        return Promise.all(promises);
    };

    // webpackJsonpCallback
    function webpackJsonpCallback(data) {
        var chunkIds = data[0];
        var moreModules = data[1];
        var moduleId, chunkId, i = 0, resolves = [];
        
        for (; i < chunkIds.length; i++) {
            chunkId = chunkIds[i];
            if (Object.prototype.hasOwnProperty.call(installedChunks, chunkId) && installedChunks[chunkId]) {
                resolves.push(installedChunks[chunkId][0]);
            }
            installedChunks[chunkId] = 0;
        }
        
        for (moduleId in moreModules) {
            if (Object.prototype.hasOwnProperty.call(moreModules, moduleId)) {
                modules[moduleId] = moreModules[moduleId];
            }
        }
        
        while (resolves.length) {
            resolves.shift()();
        }
    }

    var chunkLoadingGlobal = window["webpackJsonp_agent"] = window["webpackJsonp_agent"] || [];
    chunkLoadingGlobal.push = webpackJsonpCallback;

    // Base Path
    function detectBasePath() {
        var src = "";
        if (document.currentScript) src = document.currentScript.src;
        if (!src) {
            var scripts = document.getElementsByTagName("script");
            for (var i = scripts.length - 1; i >= 0; i--) {
                if (scripts[i].src && scripts[i].src.indexOf("agent.js") !== -1) {
                    src = scripts[i].src;
                    break;
                }
            }
        }
        if (!src) return "/m/agent/";
        return src.substring(0, src.lastIndexOf("/") + 1);
    }

    // =========================================================================
    // Main Entry
    // =========================================================================
    return function(publicPath) {
        window.__agent_base_path__ = publicPath || detectBasePath();
        console.log("[Agent Module] Base Path:", window.__agent_base_path__);

        // Async Component Definition
        var AsyncDashboard = function() {
            console.log("[Agent Module] Loading Dashboard Async...");
            return __webpack_require__.e("agent/views/views-agent-Dashboard")
                .then(function() {
                    console.log("[Agent Module] Chunk loaded, requiring module...");
                    return __webpack_require__("./views/agent/index.vue");
                })
                .catch(function(err) {
                    console.error("[Agent Module] Failed to load dashboard:", err);
                    return { render: function(h) { return h("div", "Failed to load module: " + err.message); } };
                });
        };

        return {
            router: function(menusRouter, moduleName) {
                console.log("[Agent Module] Router init with menus:", menusRouter, "moduleName:", moduleName);
                var routes = [];
                var modName = moduleName || "agent"; // Default fallback
                
                // Add index route first (High Priority)
                routes.push({
                    path: "/" + modName + "/index",
                    name: "AgentIndex",
                    component: AsyncDashboard,
                    meta: { moduleName: modName, keepAlive: true }
                });

                 // Add agent route
                routes.push({
                    path: "/" + modName + "/agent",
                    name: "AgentMain",
                    component: AsyncDashboard,
                    meta: { moduleName: modName, keepAlive: true }
                });

                for (var i = 0; i < menusRouter.length; i++) {
                    var item = menusRouter[i];
                    console.log("[Agent Module] Registering route:", item.path);
                    routes.push({
                        path: item.path,
                        name: item.label,
                        component: AsyncDashboard,
                        meta: {
                            moduleName: modName,
                            title: item.label,
                            keepAlive: true
                        }
                    });
                }
                
                return routes;
            },
            store: {}
        };
    };
}));
