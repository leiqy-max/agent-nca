import os
import shutil
import time

def build_final_demo_package(proven_source, react_dist):
    print(f"Building final demo package from proven source: {proven_source}")
    base_dir = "final-demo-pkg"
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    
    # 1. Copy EVERYTHING from the proven source (demo20260318)
    shutil.copytree(proven_source, base_dir)
    print("Copied all files (including all views and maps) from proven source.")
    
    # 2. Update agent-ui directory with the LATEST React build
    # This contains the postMessage listener in App.jsx
    agent_ui_dest = os.path.join(base_dir, "agent-ui")
    if os.path.exists(agent_ui_dest):
        shutil.rmtree(agent_ui_dest)
    os.makedirs(agent_ui_dest)
    
    print(f"Replacing agent-ui assets from {react_dist}")
    for item in os.listdir(react_dist):
        s = os.path.join(react_dist, item)
        d = os.path.join(agent_ui_dest, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    # 3. Update the agent wrapper scripts with postMessage SSO logic
    # We update BOTH the unhashed and the hashed version found in the screenshot
    views_dir = os.path.join(base_dir, "views")
    
    sso_wrapper_content = """
(function () {
    // Latest SSO Logic for iframe wrapper with handshake
    var component = {
      name: "AgentDemoWrapper",
      data: function () { return { iframeSrc: "/m/demo/agent-ui/" } }, 
      mounted: function() {
          var _this = this;
          // Listen for signal from the iframe that it is ready
          window.addEventListener('message', function(event) {
              if (event.data && event.data.type === 'IFRAME_READY') {
                  var username = "";
                  try {
                      var topDoc = window.top.document;
                      var selectors = [".el-dropdown-link", ".user-name", ".username", ".top-user-name"];
                      for(var i=0; i<selectors.length; i++) {
                          var el = topDoc.querySelector(selectors[i]);
                          if(el && el.textContent.trim()) { 
                              username = el.textContent.trim(); 
                              break; 
                          }
                      }
                  } catch(e) {
                      console.error("[SSO] Failed to access parent window:", e);
                  }

                  if (username) {
                      var iframe = _this.$el.querySelector('iframe');
                      if (iframe) {
                          console.log("[SSO] Received ready signal, posting username:", username);
                          iframe.contentWindow.postMessage({ type: 'SSO_USERNAME', username: username }, '*');
                      }
                  } else {
                      console.warn("[SSO] Could not detect username from parent window.");
                  }
              }
          });
      },
      render: function (h) {
        return h("div", { style: { height: "100%", width: "100%", overflow: "hidden" } }, [
          h("iframe", { attrs: { src: this.iframeSrc, frameborder: "0" }, style: { width: "100%", height: "100%", border: "none" } })
        ])
      }
    };

  // 关键修复：Webpack 模块定义必须使用数字 ID '3'
  var defs = {
    3: function(m, e, i) {
        m.exports = component;
        m.exports.default = component;
        m.exports.__esModule = true;
    }
  };

  // 关键修复：demo 模块必须推送到 webpackJsonp_demo
  (window.webpackJsonp_demo = window.webpackJsonp_demo || []).push([
    ["views/views-demo-agent"], 
    defs
  ]);
})();
"""
    # Overwrite the known agent files
    agent_files = ["views-demo-agent.js", "views-demo-agent.79ab08be27b716588dfd.js"]
    for filename in agent_files:
        file_path = os.path.join(views_dir, filename)
        with open(file_path, "w") as f:
            f.write(sso_wrapper_content.strip())
        print(f"Updated {filename} with latest SSO logic.")

    # 4. Create the final ZIP
    output_filename = "demo-final-20260318"
    shutil.make_archive(output_filename, "zip", root_dir=base_dir)
    print(f"Created {output_filename}.zip")
    
    # Cleanup
    shutil.rmtree(base_dir)
    return f"{output_filename}.zip"

if __name__ == "__main__":
    proven_source = "/home/leiqy/projects/demo20260318"
    react_dist = "/home/leiqy/projects/agent-nca/frontend/dist"
    
    if os.path.exists(proven_source) and os.path.exists(react_dist):
        build_final_demo_package(proven_source, react_dist)
    else:
        print(f"Error: Missing source directories. Proven: {os.path.exists(proven_source)}, React: {os.path.exists(react_dist)}")
