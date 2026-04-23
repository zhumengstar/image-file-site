#!/usr/bin/env python3
import http.server
import socketserver
import os
import json
import uuid

PORT = 8080
UPLOAD_DIR = 'uploads'

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
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
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/upload':
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' in content_type:
                boundary = content_type.split('boundary=')[1]
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                parts = post_data.split(('--' + boundary).encode())
                for part in parts:
                    if b'Content-Disposition' in part and b'filename=' in part:
                        filename_start = part.find(b'filename="') + 10
                        filename_end = part.find(b'"', filename_start)
                        if filename_end > filename_start:
                            original_filename = part[filename_start:filename_end].decode()
                            if original_filename:
                                file_data_start = part.find(b'\r\n\r\n') + 4
                                file_data_end = part.rfind(b'\r\n--')
                                if file_data_start > 4 and file_data_end > file_data_start:
                                    file_data = part[file_data_start:file_data_end]
                                    
                                    unique_id = str(uuid.uuid4())
                                    name, ext = os.path.splitext(original_filename)
                                    new_filename = f'image_{unique_id}{ext}'
                                    filepath = os.path.join(UPLOAD_DIR, new_filename)
                                    
                                    with open(filepath, 'wb') as f:
                                        f.write(file_data)
                                    
                                    self.send_response(200)
                                    self.send_header('Content-Type', 'application/json')
                                    self.send_header('Access-Control-Allow-Origin', '*')
                                    self.end_headers()
                                    response = {
                                        'url': f'/{UPLOAD_DIR}/{new_filename}',
                                        'name': new_filename
                                    }
                                    self.wfile.write(json.dumps(response).encode())
                                    return
            
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'No file uploaded'}).encode())
    
    def do_DELETE(self):
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
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'File not found'}).encode())
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True

with ThreadedHTTPServer(('', PORT), CustomHandler) as httpd:
    print(f'Server running at http://localhost:{PORT}')
    httpd.serve_forever()