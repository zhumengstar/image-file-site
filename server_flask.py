from flask import Flask, request, jsonify, send_from_directory
import os
import uuid

app = Flask(__name__)
UPLOAD_DIR = 'uploads'

# 确保上传目录存在
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# 允许跨域
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

# 静态文件服务
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# 获取图片列表
@app.route('/images')
def get_images():
    images = []
    for filename in os.listdir(UPLOAD_DIR):
        if os.path.isfile(os.path.join(UPLOAD_DIR, filename)) and filename.startswith('image_'):
            images.append({
                'name': filename,
                'url': f'http://localhost:8000/{UPLOAD_DIR}/{filename}'
            })
    return jsonify(images)

# 获取文件列表
@app.route('/files')
def get_files():
    files = []
    for filename in os.listdir(UPLOAD_DIR):
        if os.path.isfile(os.path.join(UPLOAD_DIR, filename)) and filename.startswith('file_'):
            file_size = os.path.getsize(os.path.join(UPLOAD_DIR, filename))
            files.append({
                'name': filename,
                'url': f'http://localhost:8000/{UPLOAD_DIR}/{filename}',
                'size': file_size
            })
    return jsonify(files)

# 上传文件
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' in request.files:
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # 生成唯一文件名
        unique_id = str(uuid.uuid4())
        name, ext = os.path.splitext(file.filename)
        new_filename = f'image_{unique_id}{ext}'
        filepath = os.path.join(UPLOAD_DIR, new_filename)
        
        file.save(filepath)
        
        return jsonify({
            'url': f'http://localhost:8000/{UPLOAD_DIR}/{new_filename}',
            'name': new_filename
        })
    elif 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # 生成唯一文件名
        unique_id = str(uuid.uuid4())
        name, ext = os.path.splitext(file.filename)
        new_filename = f'file_{unique_id}{ext}'
        filepath = os.path.join(UPLOAD_DIR, new_filename)
        
        file.save(filepath)
        file_size = os.path.getsize(filepath)
        
        return jsonify({
            'url': f'http://localhost:8000/{UPLOAD_DIR}/{new_filename}',
            'name': new_filename,
            'size': file_size
        })
    else:
        return jsonify({'error': 'No file uploaded'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)