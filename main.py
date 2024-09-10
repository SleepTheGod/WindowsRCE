import os
import subprocess
import shutil
import http.server
import socketserver
import sys

# Define paths and file contents
cpp_file = 'module.cpp'
wasm_file = 'module.wasm'
js_file = 'module.js'
html_file = 'index.html'
build_dir = 'build'

cpp_code = '''\
#include <emscripten/emscripten.h>
#include <cstdio>

extern "C" {

EMSCRIPTEN_KEEPALIVE
void executeOutSandbox() {
    printf("Executed outSandbox method in WebAssembly.\\n");
}

}
'''

html_content = f'''\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebAssembly Integration</title>
    <script>
        async function loadWasm() {{
            try {{
                const response = await fetch('{wasm_file}');
                const wasmArrayBuffer = await response.arrayBuffer();
                const {{ instance }} = await WebAssembly.instantiate(wasmArrayBuffer);
                return instance.exports;
            }} catch (error) {{
                console.error('Failed to load WebAssembly module:', error);
                throw error;
            }}
        }}

        async function init() {{
            try {{
                const wasmExports = await loadWasm();
                wasmExports.executeOutSandbox();
            }} catch (error) {{
                console.error('Initialization failed:', error);
            }}
        }}

        document.addEventListener('DOMContentLoaded', init);
    </script>
</head>
<body>
    <h1>WebAssembly Example</h1>
    <p>Check the console for WebAssembly output.</p>
</body>
</html>
'''

def install_python_packages():
    """Install necessary Python packages."""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'setuptools'])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Python packages: {e}")
        sys.exit(1)

def install_emscripten():
    """Install Emscripten and set up environment."""
    if shutil.which('emcc') is None:
        print("Installing Emscripten...")
        try:
            subprocess.check_call(['git', 'clone', 'https://github.com/emscripten-core/emsdk.git'])
            os.chdir('emsdk')
            subprocess.check_call(['git', 'pull'])
            if os.name == 'nt':
                subprocess.check_call(['emsdk.bat', 'install', 'latest'])
                subprocess.check_call(['emsdk.bat', 'activate', 'latest'])
                subprocess.check_call(['emsdk_env.bat'])
            else:
                subprocess.check_call(['./emsdk', 'install', 'latest'])
                subprocess.check_call(['./emsdk', 'activate', 'latest'])
                subprocess.check_call(['source', 'emsdk_env.sh'])
            os.chdir('..')
        except subprocess.CalledProcessError as e:
            print(f"Failed to install or configure Emscripten: {e}")
            sys.exit(1)
    else:
        print("Emscripten already installed.")

def compile_cpp_to_wasm():
    """Compile the C++ code to WebAssembly."""
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    with open(os.path.join(build_dir, cpp_file), 'w') as f:
        f.write(cpp_code)

    try:
        subprocess.run([
            'emcc', os.path.join(build_dir, cpp_file),
            '-o', os.path.join(build_dir, js_file),
            '-s', 'EXPORTED_FUNCTIONS=["_executeOutSandbox"]',
            '-s', 'EXPORTED_RUNTIME_METHODS=["cwrap"]'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        sys.exit(1)

def write_html():
    """Write HTML content to file."""
    with open(os.path.join(build_dir, html_file), 'w') as f:
        f.write(html_content)

def start_http_server():
    """Start HTTP server to serve files."""
    port = 8000
    os.chdir(build_dir)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving at http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server interrupted by user. Shutting down.")
            httpd.server_close()
        except Exception as e:
            print(f"Server error: {e}")
            httpd.server_close()

def main():
    """Main function to run all steps."""
    install_python_packages()
    install_emscripten()
    compile_cpp_to_wasm()
    write_html()
    start_http_server()

if __name__ == '__main__':
    main()
