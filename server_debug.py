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
            image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg']
            video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
            for filename in os.listdir(UPLOAD_DIR):
                if os.path.isfile(os.path.join(UPLOAD_DIR, filename)):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in image_extensions or ext in video_extensions:
                        file_type = 'image' if ext in image_extensions else 'video'
                        images.append({
                            'name': filename,
                            'url': f'/{UPLOAD_DIR}/{filename}',
                            'type': f'{file_type}/{ext[1:]}'
                        })
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(images).encode())
            print(f"[GET /images] Returning {len(images)} images/videos")
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
                
                # 根据文件扩展名判断文件类型
                ext = os.path.splitext(filename)[1].lower()
                
                if ext == '.pdf':
                    response = {
                        'type': 'pdf',
                        'name': filename,
                        'url': f'/{UPLOAD_DIR}/{filename}',
                        'size': os.path.getsize(filepath) // 1024
                    }
                elif ext in ['.doc', '.docx']:
                    response = {
                        'type': 'docx',
                        'name': filename,
                        'url': f'/{UPLOAD_DIR}/{filename}',
                        'size': os.path.getsize(filepath) // 1024,
                        'content': 'Word文档内容预览（仅支持基本文本）'
                    }
                elif ext in ['.xls', '.xlsx']:
                    response = {
                        'type': 'excel',
                        'name': filename,
                        'url': f'/{UPLOAD_DIR}/{filename}',
                        'size': os.path.getsize(filepath) // 1024,
                        'sheetCount': 1,
                        'sheets': [{
                            'name': 'Sheet1',
                            'rows': [[f'Cell {i+1},{j+1}' for j in range(5)] for i in range(3)]
                        }]
                    }
                elif ext in ['.txt', '.md', '.json', '.xml', '.html', '.css', '.js', '.csv']:
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        content = '无法读取文件内容（非文本文件）'
                    response = {
                        'type': 'text',
                        'name': filename,
                        'url': f'/{UPLOAD_DIR}/{filename}',
                        'size': os.path.getsize(filepath) // 1024,
                        'content': content
                    }
                else:
                    response = {
                        'type': 'unsupported',
                        'name': filename,
                        'url': f'/{UPLOAD_DIR}/{filename}',
                        'size': os.path.getsize(filepath) // 1024,
                        'message': '暂不支持此文件类型的预览'
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
                                    
                                    # 使用原始文件名，添加数字后缀以避免冲突
                                    name, ext = os.path.splitext(filename)
                                    new_filename = filename
                                    filepath = os.path.join(UPLOAD_DIR, new_filename)
                                    
                                    # 如果文件已存在，添加数字后缀
                                    counter = 1
                                    while os.path.exists(filepath):
                                        new_filename = f'{name}_{counter}{ext}'
                                        filepath = os.path.join(UPLOAD_DIR, new_filename)
                                        counter += 1
                                    
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