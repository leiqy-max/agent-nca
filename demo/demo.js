(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
    typeof define === 'function' && define.amd ? define(factory) :
    (global.m_demo = factory());
}(this, function () {
    console.log("[Demo Module] Initializing... Build Time: 1773824904");

    var chunkLoadingGlobal = window["webpackJsonp_demo"] = window["webpackJsonp_demo"] || [];
    var installedChunks = {};
    var modules = {};

    function webpackJsonpCallback(data) {
        var chunkIds = data[0];
        var moreModules = data[1];
        var moduleId, chunkId, i = 0, resolves = [];
        
        for(moduleId in moreModules) {
            if(Object.prototype.hasOwnProperty.call(moreModules, moduleId)) {
                modules[moduleId] = moreModules[moduleId];
            }
        }

        for(i = 0; i < chunkIds.length; i++) {
            chunkId = chunkIds[i];
            if(Object.prototype.hasOwnProperty.call(installedChunks, chunkId) && installedChunks[chunkId]) {
                resolves.push(installedChunks[chunkId][0]);
            }
            installedChunks[chunkId] = 0; 
        }
        
        while(resolves.length) {
            resolves.shift()();
        }
    };

    var existingPush = chunkLoadingGlobal.push;
    chunkLoadingGlobal.push = webpackJsonpCallback;
    var copy = chunkLoadingGlobal.slice();
    for(var i=0; i<copy.length; i++) {
        webpackJsonpCallback(copy[i]);
    }

    function __webpack_require__(moduleId) {
        var module = { exports: {} };
        if(modules[moduleId]) {
            modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
        } else {
            console.error("[Demo Module] Module not found:", moduleId, "Available:", Object.keys(modules));
        }
        return module.exports;
    };

    function getUrlParams(paramStr) {
        var paramsObj = {};
        if (paramStr && paramStr.indexOf("?") != -1) {
            var str = paramStr.split("?")[1];
            var paramArr = str.split("&");
            for(var i = 0; i < paramArr.length; i ++) {
                if(paramArr[i].indexOf("=") != -1) {
                    paramsObj[paramArr[i].split("=")[0]] = unescape(paramArr[i].split("=")[1]);
                }
            }
        }
        return paramsObj;
    }

    return function(publicPath) {
        console.log("[Demo Module] Factory called. PublicPath:", publicPath);
        
        return {
            router: function(menusRouter, moduleName) {
                console.log("[Demo Module] Router processing", menusRouter.length, "routes. ModuleName:", moduleName);
                
                return menusRouter.map(function(item) {
                    var props = {};
                    var route = {
                        name: item.label,
                        path: item.path,
                        props: props,
                        query: {} ,
                        meta: {
                            keepAlive: Number(item['keepAlive']) === 1,
                            moduleName: moduleName,
                            name: item.label,
                            resource: item.resource || [],
                            defaultParams: { grayMode: "" },
                            inputParams: { userId: "", tenantId: "" }
                        }
                    };

                    if (typeof nc !== 'undefined' && nc.util && nc.util.getStore) {
                        var userInfo = nc.util.getStore({name:"userInfo"});
                        if (userInfo) {
                            route.meta.inputParams.userId = userInfo.id;
                            route.meta.inputParams.tenantId = userInfo.tenantId;
                        }
                    }

                    var realPath = item.path;
                    if (realPath.indexOf('/' + moduleName) === 0) {
                        realPath = realPath.replace('/' + moduleName, '');
                    }
                    
                    var params = getUrlParams(item.path);
                    if(params) {
                        route.props = params;
                        Object.assign(route.meta.inputParams, params);
                    }

                    route.component = function() {
                        console.log("[Demo Module] Loading component for:", item.path);
                        return new Promise(function(resolve, reject) {
                            if(modules["demo/views/agent"]) {
                                resolve(__webpack_require__("demo/views/agent"));
                                return;
                            }
                            
                            var resolveWrapper = function() {
                                try {
                                    var component = __webpack_require__("demo/views/agent");
                                    resolve(component);
                                } catch(e) {
                                    reject(e);
                                }
                            };

                            installedChunks["demo/views/agent"] = [resolveWrapper, reject];
                            
                            var script = document.createElement('script');
                            // Ensure this path matches Nginx location
                            script.src = '/m/demo/views/views-demo-agent.js?v=1773824904';
                            script.onerror = function(e) {
                                reject(e);
                            };
                            document.head.appendChild(script);
                        });
                    };

                    return route;
                });
            },
            store: {}
        };
    };
}));