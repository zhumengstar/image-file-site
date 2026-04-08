import http.server
import socketserver
import os
import cgi
import json
from urllib.parse import urlparse, parse_qs

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
                        'url': f'http://localhost:{PORT}/{UPLOAD_DIR}/{filename}'
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
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            if 'image' in form:
                fileitem = form['image']
                if fileitem.file:
                    # 保存文件
                    filename = fileitem.filename
                    if filename:
                        # 生成唯一文件名
                        import time
                        import random
                        unique_suffix = str(int(time.time())) + '_' + str(random.randint(1, 10000))
                        name, ext = os.path.splitext(filename)
                        new_filename = f'image_{unique_suffix}{ext}'
                        filepath = os.path.join(UPLOAD_DIR, new_filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(fileitem.file.read())
                        
                        # 返回响应
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        response = {
                            'url': f'http://localhost:{PORT}/{UPLOAD_DIR}/{new_filename}',
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

# 启动服务器
handler = MyHTTPRequestHandler
handler.directory = '.'

with socketserver.TCPServer(('', PORT), handler) as httpd:
    print(f'Server running at http://localhost:{PORT}')
    httpd.serve_forever()