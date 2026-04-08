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
    cb(null, file.fieldname + '-' + uniqueSuffix + ext);
  }
});

const upload = multer({ storage });

// 静态文件服务
app.use('/uploads', express.static(uploadDir));
app.use(express.static(__dirname));

// 上传图片
app.post('/upload', upload.single('image'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }
  
  const imageUrl = `http://localhost:3001/uploads/${req.file.filename}`;
  res.json({ url: imageUrl, name: req.file.filename });
});

// 获取图片列表
app.get('/images', (req, res) => {
  fs.readdir(uploadDir, (err, files) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to read upload directory' });
    }
    
    const images = files.map(file => ({
      name: file,
      url: `http://localhost:3001/uploads/${file}`
    }));
    res.json(images);
  });
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});