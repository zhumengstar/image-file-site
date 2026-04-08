# 图床网站 (Image File Site)

一个功能强大、界面美观的图床网站，支持多种上传方式，包括拖拽、点击和粘贴截图，方便用户快速分享图片。

## 功能特点

### 📤 多种上传方式
- **拖拽上传**：直接将图片拖拽到上传区域
- **点击上传**：点击上传区域选择本地图片
- **粘贴上传**：直接粘贴截图（Ctrl+V 或 Command+V）

### 📁 图片管理
- **列表视图**：以列表形式展示图片，包含缩略图和文件名
- **瀑布流视图**：以网格形式展示图片，更直观
- **图片预览**：点击图片显示大图，点击背景关闭
- **文件名显示**：鼠标悬停显示完整文件名

### 🔗 链接复制
- **复制链接**：复制图片的直接链接
- **复制 Markdown**：复制 Markdown 格式的图片链接，方便在文档中使用

### 🎨 界面设计
- **现代化深色主题**：美观、护眼
- **响应式布局**：适配不同屏幕尺寸
- **平滑动画**：增强用户体验
- **固定侧边栏**：方便快速访问图片列表

### 💾 数据持久化
- 图片保存在服务器的 `uploads` 目录中
- 重启服务器后图片仍然存在
- 支持多用户访问

## 技术实现

### 前端
- **框架**：React 18 + Babel + CDN
- **样式**：CSS3 (使用 CSS 变量实现主题)
- **动画**：CSS 动画和过渡效果

### 后端
- **服务器**：Flask (Python)
- **存储**：本地文件系统 (`uploads` 目录)
- **API**：
  - `POST /upload` - 上传图片
  - `GET /images` - 获取图片列表

## 快速开始

### 环境要求
- Python 3.6+
- Flask

### 安装和运行

1. **克隆仓库**
```bash
git clone https://github.com/zhumengstar/image-file-site.git
cd image-file-site
```

2. **安装依赖**
```bash
pip3 install flask
```

3. **启动服务器**
```bash
python3 server_flask.py
```

4. **访问网站**
打开浏览器访问 `http://localhost:8000`

## 使用指南

### 上传图片
1. 打开网站 `http://localhost:8000`
2. 选择一种上传方式：
   - 拖拽图片到上传区域
   - 点击上传区域选择本地图片
   - 直接粘贴截图（Ctrl+V 或 Command+V）

### 管理图片
1. 左侧边栏显示已上传的图片列表
2. 点击"列表"或"瀑布流"按钮切换视图模式
3. 点击图片查看大图预览
4. 点击背景关闭预览

### 复制链接
1. 找到要分享的图片
2. 点击"复制链接"按钮复制直接链接
3. 点击"Markdown"按钮复制 Markdown 格式链接
4. 链接会自动复制到剪贴板

## 项目结构

```
image-file-site/
├── index.html          # 前端页面
├── server_flask.py     # Flask 服务器
├── server.py           # 原始 Python 服务器
├── server.js           # Node.js 服务器
├── package.json        # 项目配置
├── vite.config.js      # Vite 配置
├── src/                # React 源代码
│   ├── App.jsx         # 主应用组件
│   ├── main.jsx        # 应用入口
│   └── index.css       # 样式文件
├── uploads/            # 图片存储目录
└── README.md           # 项目说明
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- GitHub: [zhumengstar](https://github.com/zhumengstar)

---

**享受使用图床网站！** 🎉