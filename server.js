const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();
const port = 3001;

// 确保上传目录存在
const uploadDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// 配置 multer 存储
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    const ext = path.extname(file.originalname);
    const prefix = file.mimetype.startsWith('video/') ? 'video' : 'image';
    cb(null, prefix + '-' + uniqueSuffix + ext);
  }
});

const upload = multer({ storage, limits: { fileSize: 500 * 1024 * 1024 } }); // 500MB limit

// 静态文件服务
app.use('/uploads', express.static(uploadDir));
app.use('/videos', express.static(uploadDir));
app.use(express.static(__dirname));

// 上传图片/视频
app.post('/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }
  
  const url = `http://localhost:3001/uploads/${req.file.filename}`;
  res.json({ url: url, name: req.file.filename, type: req.file.mimetype });
});

// 获取图片列表
app.get('/images', (req, res) => {
  fs.readdir(uploadDir, (err, files) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to read upload directory' });
    }
    
    const getMimeType = (filename) => {
      const ext = path.extname(filename).toLowerCase();
      const videoExts = ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.wmv', '.flv'];
      const imageExts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'];
      
      if (videoExts.includes(ext)) return 'video/' + ext.slice(1);
      if (imageExts.includes(ext)) return 'image/' + ext.slice(1);
      return 'application/octet-stream';
    };
    
    const images = files.map(file => ({
      name: file,
      url: `http://localhost:3001/uploads/${file}`,
      type: getMimeType(file)
    }));
    res.json(images);
  });
});

// 删除图片
app.delete('/images/:filename', (req, res) => {
  const filename = decodeURIComponent(req.params.filename);
  const filePath = path.join(uploadDir, filename);
  
  fs.unlink(filePath, (err) => {
    if (err) {
      console.error('Delete error:', err);
      return res.status(500).json({ error: 'Failed to delete file: ' + err.message });
    }
    res.json({ success: true });
  });
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});