const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();
const port = 3001;

// 预览功能依赖
let mammoth, XLSX;
try {
  mammoth = require('mammoth');
  XLSX = require('xlsx');
} catch (e) {
  console.warn('Some preview modules not available:', e.message);
}

// 确保上传目录存在
const uploadDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// 文件名映射文件
const nameMapFile = path.join(__dirname, 'uploads', 'file-names.json');

// 正确处理文件名编码，处理中文
const decodeFileName = (filename) => {
  if (!filename) return '';
  
  if (Buffer.isBuffer(filename)) {
    // 如果是 Buffer，直接尝试 UTF-8 解码
    return filename.toString('utf8');
  }
  
  if (typeof filename === 'string') {
    // 字符串可能是 Latin-1 编码的字节序列，需要转换
    // 如果字符串包含非 ASCII 字符，可能是编码问题
    const buf = Buffer.from(filename, 'binary');
    const utf8Str = buf.toString('utf8');
    
    // 如果转换后是有效的 UTF-8（不包含 Latin-1 特有的字符），使用转换后的
    // 否则返回原字符串
    if (/[\u0080-\uFFFF]/.test(utf8Str) || /[\u4e00-\u9fa5]/.test(utf8Str)) {
      return utf8Str;
    }
    return filename;
  }
  
  return String(filename);
};

// 读取/初始化文件名映射
const readNameMap = () => {
  try {
    if (fs.existsSync(nameMapFile)) {
      const content = fs.readFileSync(nameMapFile, 'utf8');
      return JSON.parse(content);
    }
  } catch (e) {
    console.error('Error reading name map:', e);
  }
  return {};
};

const saveNameMap = (map) => {
  try {
    const data = JSON.stringify(map, null, 2);
    fs.writeFileSync(nameMapFile, data, 'utf8');
  } catch (e) {
    console.error('Error saving name map:', e);
  }
};

// 配置 multer 存储
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    const ext = path.extname(file.originalname);
    const mimeType = file.mimetype;
    
    // 根据 MIME 类型选择前缀
    let prefix = 'file';
    if (mimeType.startsWith('image/')) {
      prefix = 'image';
    } else if (mimeType.startsWith('video/')) {
      prefix = 'video';
    }
    
    cb(null, prefix + '-' + uniqueSuffix + ext);
  }
});

const upload = multer({ storage, limits: { fileSize: 500 * 1024 * 1024 } }); // 500MB limit

// 静态文件服务
app.use('/uploads', express.static(uploadDir));
app.use('/videos', express.static(uploadDir));
app.use(express.static(__dirname));

// 设置 JSON 响应编码
app.set('json spaces', 2);

// 上传图片/视频
app.post('/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }
  
  // 正确解码文件名
  const originalName = decodeFileName(req.file.originalname);
  
  // 保存原始文件名映射
  const nameMap = readNameMap();
  nameMap[req.file.filename] = originalName;
  saveNameMap(nameMap);
  
  const url = `http://localhost:3001/uploads/${req.file.filename}`;
  
  // 设置响应头确保 UTF-8 编码
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.json({ url: url, name: req.file.filename, originalName: originalName, type: req.file.mimetype });
});

// 获取图片/视频列表
app.get('/images', (req, res) => {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
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
    
    const nameMap = readNameMap();
    
    // 只返回 image- 和 video- 前缀的文件，按修改时间倒序（最新的在前）
    const imageFiles = files.filter(file => file.startsWith('image-') || file.startsWith('video-'));
    
    // 获取文件信息并按修改时间排序
    Promise.all(imageFiles.map(file => {
      return new Promise((resolve) => {
        fs.stat(path.join(uploadDir, file), (err, stats) => {
          resolve({
            name: file,
            url: `http://localhost:3001/uploads/${file}`,
            type: getMimeType(file),
            originalName: nameMap[file] || file,
            mtime: stats ? stats.mtime.getTime() : 0
          });
        });
      });
    }))
    .then(results => {
      results.sort((a, b) => b.mtime - a.mtime);
      res.json(results);
    });
  });
});

// 获取普通文件列表（非图片/视频）
app.get('/files', (req, res) => {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  fs.readdir(uploadDir, (err, files) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to read upload directory' });
    }
    
    const getMimeType = (filename) => {
      const ext = path.extname(filename).toLowerCase();
      const mimeTypes = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.txt': 'text/plain',
        '.zip': 'application/zip',
        '.rar': 'application/x-rar-compressed',
        '.7z': 'application/x-7z-compressed',
        '.tar': 'application/x-tar',
        '.gz': 'application/gzip',
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.csv': 'text/csv',
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.apk': 'application/vnd.android.package-archive',
        '.ipa': 'application/octet-stream',
        '.dmg': 'application/x-apple-diskimage',
        '.pkg': 'application/x-newton-compatible-pkg',
        '.deb': 'application/x-debian-package',
        '.rpm': 'application/x-redhat-package-manager',
        '.dll': 'application/x-msdownload',
        '.exe': 'application/x-msdownload',
        '.sh': 'application/x-sh'
      };
      return mimeTypes[ext] || 'application/octet-stream';
    };
    
    // 排除图片和视频扩展名，以及文件名映射文件
    const excludedExts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', 
                          '.mp4', '.webm', '.mov', '.avi', '.mkv', '.wmv', '.flv'];
    
    const nameMap = readNameMap();
    
    // 只返回非图片/视频的文件
    const filteredFiles = files.filter(file => {
      const ext = path.extname(file).toLowerCase();
      return !excludedExts.includes(ext) && ext !== '.json';
    });
    
    // 获取文件信息并按修改时间排序
    Promise.all(filteredFiles.map(file => {
      return new Promise((resolve) => {
        fs.stat(path.join(uploadDir, file), (err, stats) => {
          resolve({
            name: file,
            originalName: nameMap[file] || file,
            url: `http://localhost:3001/uploads/${file}`,
            type: getMimeType(file),
            mtime: stats ? stats.mtime.getTime() : 0
          });
        });
      });
    }))
    .then(results => {
      results.sort((a, b) => b.mtime - a.mtime);  // 按修改时间倒序
      res.json(results);
    });
  });
});

// 删除图片/视频
app.delete('/images/:filename', (req, res) => {
  const filename = decodeURIComponent(req.params.filename);
  const filePath = path.join(uploadDir, filename);
  
  // 同时删除文件名映射
  const nameMap = readNameMap();
  delete nameMap[filename];
  saveNameMap(nameMap);
  
  fs.unlink(filePath, (err) => {
    if (err) {
      console.error('Delete error:', err);
      return res.status(500).json({ error: 'Failed to delete file: ' + err.message });
    }
    res.json({ success: true });
  });
});

// 删除普通文件
app.delete('/files/:filename', (req, res) => {
  const filename = decodeURIComponent(req.params.filename);
  const filePath = path.join(uploadDir, filename);
  
  // 同时删除文件名映射
  const nameMap = readNameMap();
  delete nameMap[filename];
  saveNameMap(nameMap);
  
  fs.unlink(filePath, (err) => {
    if (err) {
      console.error('Delete error:', err);
      return res.status(500).json({ error: 'Failed to delete file: ' + err.message });
    }
    res.json({ success: true });
  });
});

// 文件预览 API
app.get('/preview/:filename', async (req, res) => {
  const filename = decodeURIComponent(req.params.filename);
  const filePath = path.join(uploadDir, filename);
  const ext = path.extname(filename).toLowerCase();
  
  try {
    const dataBuffer = fs.readFileSync(filePath);
    const nameMap = readNameMap();
    const originalName = nameMap[filename] || filename;
    
    // 获取文件大小
    const stats = fs.statSync(filePath);
    const fileSizeKB = (stats.size / 1024).toFixed(2);
    
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    
    // PDF 预览（显示文件信息）
    if (ext === '.pdf') {
      res.json({
        type: 'pdf',
        name: originalName,
        size: fileSizeKB,
        message: 'PDF 文件，请下载后查看',
        url: `http://localhost:3001/uploads/${filename}`
      });
      return;
    }
    
    // Word 预览
    if (ext === '.docx') {
      try {
        const result = await mammoth.extractRawText({ buffer: dataBuffer });
        res.json({
          type: 'docx',
          name: originalName,
          size: fileSizeKB,
          content: result.value.substring(0, 50000)
        });
      } catch (e) {
        res.json({ type: 'unsupported', name: originalName, message: 'Word 文档解析失败' });
      }
      return;
    }
    
    // Excel 预览
    if (ext === '.xlsx' || ext === '.xls') {
      try {
        const workbook = XLSX.read(dataBuffer, { type: 'buffer' });
        const sheets = workbook.SheetNames.map(sheetName => {
          const sheet = workbook.Sheets[sheetName];
          const data = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });
          return {
            name: sheetName,
            rows: data.slice(0, 100) // 只取前100行
          };
        });
        res.json({
          type: 'excel',
          name: originalName,
          size: fileSizeKB,
          sheetCount: workbook.SheetNames.length,
          sheets: sheets
        });
      } catch (e) {
        res.json({ type: 'unsupported', name: originalName, message: 'Excel 解析失败' });
      }
      return;
    }
    
    // 文本文件
    const textExts = ['.txt', '.json', '.xml', '.csv', '.html', '.css', '.js', '.md', '.log', '.yml', '.yaml', '.sh', '.py', '.java', '.c', '.cpp', '.h', '.ts', '.jsx', '.tsx'];
    if (textExts.includes(ext)) {
      try {
        const content = dataBuffer.toString('utf8');
        res.json({
          type: 'text',
          name: originalName,
          size: fileSizeKB,
          content: content.substring(0, 100000)
        });
      } catch (e) {
        res.json({ type: 'unsupported', name: originalName, message: '文件读取失败' });
      }
      return;
    }
    
    // 图片
    const imageExts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico'];
    if (imageExts.includes(ext)) {
      res.json({
        type: 'image',
        name: originalName,
        size: fileSizeKB,
        url: `http://localhost:3001/uploads/${filename}`
      });
      return;
    }
    
    // 不支持的文件类型
    res.json({ type: 'unsupported', name: originalName, message: '此文件类型不支持预览' });
    
  } catch (err) {
    console.error('Preview error:', err);
    res.status(500).json({ error: '预览失败: ' + err.message });
  }
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});