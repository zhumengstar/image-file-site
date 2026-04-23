import http.server
import socketserver
import os
import json
import uuid
from urllib.parse import urlparse

PORT = 8000
UPLOAD_DIR = 'uploads'

# 确保上传目录存在
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/images':
            # 获取图片列表
            images = []
            for filename in os.listdir(UPLOAD_DIR):
                if os.path.isfile(os.path.join(UPLOAD_DIR, filename)):
                    images.append({
                        'name': filename,
                        'url': f'/{UPLOAD_DIR}/{filename}'
                    })
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(images).encode())
        else:
            # 静态文件服务
            self.send_header('Access-Control-Allow-Origin', '*')
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/upload':
            # 处理文件上传
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # 解析multipart/form-data
            boundary = self.headers['Content-Type'].split('boundary=')[1].encode()
            parts = post_data.split(boundary)
            
            for part in parts:
                if b'Content-Disposition' in part:
                    # 查找文件名
                    content_disposition = part.split(b'\r\n')[1]
                    if b'filename="' in content_disposition:
                        filename = content_disposition.split(b'filename="')[1].split(b'"')[0].decode()
                        if filename:
                            # 生成唯一文件名
                            unique_id = str(uuid.uuid4())
                            name, ext = os.path.splitext(filename)
                            new_filename = f'image_{unique_id}{ext}'
                            filepath = os.path.join(UPLOAD_DIR, new_filename)
                            
                            # 提取文件内容
                            file_content = part.split(b'\r\n\r\n')[1].split(b'\r\n--')[0]
                            
                            # 保存文件
                            with open(filepath, 'wb') as f:
                                f.write(file_content)
                            
                            # 返回响应
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            response = {
                                'url': f'/{UPLOAD_DIR}/{new_filename}',
                                'name': new_filename
                            }
                            self.wfile.write(json.dumps(response).encode())
                            return
            
            # 上传失败
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {'error': 'No file uploaded'}
            self.wfile.write(json.dumps(response).encode())
    
    def do_DELETE(self):
        if self.path.startswith('/images/'):
            # 处理删除图片
            filename = self.path.split('/images/')[-1]
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {'success': True}
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {'error': 'File not found'}
                self.wfile.write(json.dumps(response).encode())

# 启动服务器
handler = MyHTTPRequestHandler
handler.directory = '.'

with socketserver.TCPServer(('', PORT), handler) as httpd:
    print(f'Server running at http://localhost:{PORT}')
    httpd.serve_forever()