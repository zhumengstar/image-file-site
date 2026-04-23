#!/usr/bin/env python3
import http.server
import socketserver
import os
import json
import uuid
import io
import sys

# 默认端口
DEFAULT_PORT = 8080

# 从命令行参数获取端口
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
UPLOAD_DIR = 'uploads'

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"[GET] {self.path}")
        if self.path == '/images':
            images = []
            for filename in os.listdir(UPLOAD_DIR):
                if os.path.isfile(os.path.join(UPLOAD_DIR, filename)):
                    images.append({
                        'name': filename,
                        'url': f'/{UPLOAD_DIR}/{filename}'
                    })
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(images).encode())
            print(f"[GET /images] Returning {len(images)} images")
        elif self.path == '/files':
            files = []
            for filename in os.listdir(UPLOAD_DIR):
                if os.path.isfile(os.path.join(UPLOAD_DIR, filename)):
                    files.append({
                        'name': filename,
                        'originalName': filename,
                        'url': f'/{UPLOAD_DIR}/{filename}'
                    })
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(files).encode())
            print(f"[GET /files] Returning {len(files)} files")
        elif self.path.startswith('/preview/'):
            filename = self.path.split('/preview/')[1]
            filename = filename.split('?')[0]
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            if os.path.exists(filepath):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {
                    'type': 'text',
                    'name': filename,
                    'url': f'/{UPLOAD_DIR}/{filename}',
                    'size': os.path.getsize(filepath) // 1024
                }
                self.wfile.write(json.dumps(response).encode())
                print(f"[GET /preview/{filename}] Success")
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'File not found'}).encode())
        else:
            super().do_GET()
    
    def do_POST(self):
        print(f"[POST] {self.path}")
        if self.path == '/upload':
            try:
                content_type = self.headers.get('Content-Type', '')
                print(f"[POST /upload] Content-Type: {content_type}")
                content_length = int(self.headers.get('Content-Length', 0))
                print(f"[POST /upload] Content-Length: {content_length}")
                post_data = self.rfile.read(content_length)
                print(f"[POST /upload] Read {len(post_data)} bytes")
                
                if 'multipart/form-data' in content_type:
                    boundary = content_type.split('boundary=')[1].strip()
                    print(f"[POST /upload] Boundary: {boundary}")
                    parts = post_data.split(('--' + boundary).encode())
                    print(f"[POST /upload] Found {len(parts)} parts")
                    
                    for i, part in enumerate(parts):
                        if b'Content-Disposition' in part and b'filename=' in part:
                            print(f"[POST /upload] Processing part {i}")
                            headers_end = part.find(b'\r\n\r\n')
                            if headers_end > 0:
                                headers = part[:headers_end].decode()
                                filename_start = headers.find('filename="') + 10
                                filename_end = headers.find('"', filename_start)
                                
                                if filename_end > filename_start:
                                    filename = headers[filename_start:filename_end]
                                    print(f"[POST /upload] Filename: {filename}")
                                    file_data = part[headers_end + 4:]
                                    print(f"[POST /upload] File data size: {len(file_data)} bytes")
                                    
                                    unique_id = str(uuid.uuid4())
                                    name, ext = os.path.splitext(filename)
                                    new_filename = f'image_{unique_id}{ext}'
                                    filepath = os.path.join(UPLOAD_DIR, new_filename)
                                    
                                    with open(filepath, 'wb') as f:
                                        f.write(file_data)
                                    
                                    print(f"[POST /upload] Saved file: {filepath}")
                                    
                                    self.send_response(200)
                                    self.send_header('Content-Type', 'application/json')
                                    self.send_header('Access-Control-Allow-Origin', '*')
                                    self.end_headers()
                                    response = {
                                        'url': f'/{UPLOAD_DIR}/{new_filename}',
                                        'name': new_filename
                                    }
                                    self.wfile.write(json.dumps(response).encode())
                                    print(f"[POST /upload] Success: {response}")
                                    return
                
                print("[POST /upload] No valid file found")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No file uploaded'}).encode())
            except Exception as e:
                print(f"[POST /upload] Error: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_DELETE(self):
        print(f"[DELETE] {self.path}")
        if self.path.startswith('/images/'):
            filename = self.path.split('/images/')[1]
            filename = filename.split('?')[0]
            filename = filename.split('%2F')[-1]
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
                print(f"[DELETE] Deleted: {filepath}")
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'File not found'}).encode())
                print(f"[DELETE] Not found: {filepath}")
        elif self.path.startswith('/files/'):
            filename = self.path.split('/files/')[1]
            filename = filename.split('?')[0]
            filename = filename.split('%2F')[-1]
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
                print(f"[DELETE] Deleted: {filepath}")
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'File not found'}).encode())
                print(f"[DELETE] Not found: {filepath}")
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True

print(f'Starting server on port {PORT}...')
with ThreadedHTTPServer(('', PORT), CustomHandler) as httpd:
    print(f'Server running at http://localhost:{PORT}')
    httpd.serve_forever()