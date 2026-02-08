import os
import shutil
import zipfile
import re

def generate_agent_js(demo_js_path, output_path):
    with open(demo_js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace m_demo -> m_agent
    content = content.replace("m_demo", "m_agent")
    
    # 2. Replace webpackJsonp_demo -> webpackJsonp_agent
    content = content.replace("webpackJsonp_demo", "webpackJsonp_agent")
    
    # 3. Replace the module mapping object
    # Pattern: var n={...};function r(e)
    # We want to replace the dictionary content.
    # The dictionary looks like: {"./views/demo/Dashboard":[3,"demo/views/views-demo-Dashboard"],...}
    
    # We'll construct a new mapping for our agent view
    # We map "./views" (for root path) and "./views/agent/index" (just in case)
    new_mapping = '{' + \
        '"./views":[1,"agent/views/views-agent-index"],' + \
        '"./views/":[1,"agent/views/views-agent-index"],' + \
        '"./views/agent/index":[1,"agent/views/views-agent-index"]' + \
    '}'
    
    # Regex to find the mapping object definition
    # It usually starts with var n={ and ends with };function
    # But since it's minified, it might be tricky. 
    # Let's rely on the structure `var n={"./views/demo/Dashboard"`
    
    pattern = r'var n=\{[^}]+\};'
    match = re.search(pattern, content)
    if match:
        print("Found mapping object, replacing...")
        content = content.replace(match.group(0), f'var n={new_mapping};')
    else:
        print("Warning: Could not find mapping object via regex, trying simple string replacement if possible or failing.")
        # Fallback: if we can't find it, we might be looking at a different file version.
        # Let's try to find the start of the object
        start_marker = 'var n={"'
        end_marker = '};function'
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker, start_idx)
        if start_idx != -1 and end_idx != -1:
             content = content[:start_idx] + f'var n={new_mapping}' + content[end_idx:]

    # 4. Update the chunk URL generation logic
    # The demo.js has: return r.p+""+({...}[e]||e)+"."+{...}[e]+".js"
    # We want to simplify this to just return the chunk name + .js, since we are not using hashes.
    # We can replace the whole s.src assignment function.
    # Pattern: s.src=function(e){return r.p+""+({...}[e]||e)+"."+{...}[e]+".js"}(e);
    
    # Actually, if we just ensure our mapping object is correct, and we provide a "hash" map that returns empty string?
    # The code is: `+({...}[e]||e)+"."+{...}[e]+".js"`
    # The first map is for the path, the second map is for the hash.
    # If we change the code to not use the second map, that's better.
    
    # Let's find `s.src=function(e){`
    src_func_pattern = r's\.src=function\(e\)\{return r\.p\+""\+\(\{.*?\}\[e\]\|\|e\)\+"\."\+\(\{.*?\}\[e\]\)\+"\.js"\}\(e\)'
    
    # New function: just return module name + .js
    # We assume the module name in the mapping (e.g., "agent/views/views-agent-index") is the full path we want.
    # Note: r.p is the public path.
    new_src_func = 's.src=function(e){return r.p+e+".js"}(e)'
    
    # Use regex to replace
    content = re.sub(src_func_pattern, new_src_func, content)
    
    # 5. Replace [Demo-Lite] logs
    content = content.replace("[Demo-Lite]", "[Agent-Lite]")
    
    # 6. Replace "demo" string in router logic if necessary
    # `if("demo"!==o` -> `if("agent"!==o`
    content = content.replace('"demo"!==o', '"agent"!==o')
    content = content.replace('"/demo"+m', '"/agent"+m')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Generated {output_path}")

def build_intranet():
    project_root = os.getcwd()
    frontend_dist = os.path.join(project_root, "frontend", "dist")
    
    # Define build output structure
    build_dir = os.path.join(project_root, "build_output")
    
    # 1. agent-ui directory (React App)
    agent_ui_dir = os.path.join(build_dir, "agent-ui")
    
    # 2. agent directory (NC Framework Module)
    agent_dir = os.path.join(build_dir, "agent")
    agent_views_dir = os.path.join(agent_dir, "views")
    
    zip_filename = "agent-ui.zip"

    print(f"Starting build from {project_root}...")

    # Clean up previous build
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    
    # Create directories
    os.makedirs(agent_ui_dir)
    os.makedirs(agent_views_dir)

    # Copy Frontend Build to agent-ui
    if not os.path.exists(frontend_dist):
        print(f"Error: {frontend_dist} does not exist.")
        return

    # Copy contents of dist to agent-ui
    for item in os.listdir(frontend_dist):
        s = os.path.join(frontend_dist, item)
        d = os.path.join(agent_ui_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    # Generate agent.js
    # We need a source demo.js. We can assume it's at a fixed path or provided.
    # In this env, we know where it is.
    demo_js_path = "/home/leiqy/projects/demo-nccm-lite/deploy/frontend/demo.js"
    agent_js_path = os.path.join(agent_dir, "agent.js")
    
    if os.path.exists(demo_js_path):
        generate_agent_js(demo_js_path, agent_js_path)
    else:
        print(f"Error: Could not find {demo_js_path} to use as template!")
        return

    # Copy views-agent-index.js
    source_js = os.path.join(project_root, "frontend", "public", "views", "agent", "views-agent-index.js")
    dest_js = os.path.join(agent_views_dir, "views-agent-index.js")
    
    if os.path.exists(source_js):
        shutil.copy2(source_js, dest_js)
        print(f"Copied {source_js} to {dest_js}")
    else:
        print(f"Error: {source_js} not found!")

    # Create Zip
    print(f"Creating {zip_filename}...")
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, build_dir)
                zipf.write(file_path, arcname)
                print(f"Adding: {arcname}")

    # Clean up build dir
    shutil.rmtree(build_dir)
    print(f"Build completed: {zip_filename}")

if __name__ == "__main__":
    build_intranet()
