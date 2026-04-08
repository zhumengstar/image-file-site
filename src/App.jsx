import { useState, useEffect, useRef } from 'react'

function App() {
  const [images, setImages] = useState([])
  const [isDragging, setIsDragging] = useState(false)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState('')
  const fileInputRef = useRef(null)

  // 从本地存储加载图片
  useEffect(() => {
    const savedImages = localStorage.getItem('images')
    if (savedImages) {
      setImages(JSON.parse(savedImages))
    }
  }, [])

  // 保存图片到本地存储
  useEffect(() => {
    localStorage.setItem('images', JSON.stringify(images))
  }, [images])

  // 处理图片上传
  const handleUpload = (files) => {
    const uploadedImages = []
    
    Array.from(files).forEach((file) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onload = (e) => {
          const imageUrl = e.target.result
          const newImage = {
            id: Date.now() + Math.random(),
            url: imageUrl,
            name: file.name
          }
          setImages(prev => [...prev, newImage])
          showMessage('图片上传成功！', 'success')
        }
        reader.readAsDataURL(file)
      }
    })
  }

  // 处理拖拽事件
  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files.length > 0) {
      handleUpload(e.dataTransfer.files)
    }
  }

  // 处理点击上传
  const handleClickUpload = () => {
    fileInputRef.current.click()
  }

  // 处理文件选择
  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      handleUpload(e.target.files)
    }
  }

  // 处理粘贴上传
  useEffect(() => {
    const handlePaste = (e) => {
      const items = e.clipboardData.items
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.startsWith('image/')) {
          const file = items[i].getAsFile()
          if (file) {
            handleUpload([file])
          }
          break
        }
      }
    }

    window.addEventListener('paste', handlePaste)
    return () => window.removeEventListener('paste', handlePaste)
  }, [])

  // 复制图片链接
  const copyImageUrl = (url) => {
    navigator.clipboard.writeText(url)
      .then(() => {
        showMessage('链接已复制到剪贴板！', 'success')
      })
      .catch(() => {
        showMessage('复制失败，请手动复制！', 'error')
      })
  }

  // 显示消息
  const showMessage = (text, type) => {
    setMessage(text)
    setMessageType(type)
    setTimeout(() => {
      setMessage('')
      setMessageType('')
    }, 2000)
  }

  // 生成图片的 Markdown 格式链接
  const getMarkdownLink = (url) => {
    return `![图片](${url})`
  }

  return (
    <div className="App">
      <h1>图床网站</h1>
      <p>支持拖拽、点击或粘贴上传图片</p>
      
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />

      <div
        className={`upload-container ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClickUpload}
      >
        <h3>点击或拖拽图片到此处上传</h3>
        <p>也可以直接粘贴截图（Ctrl+V 或 Command+V）</p>
      </div>

      {message && (
        <div className={messageType === 'success' ? 'success-message' : 'error-message'}>
          {message}
        </div>
      )}

      <h2>已上传图片</h2>
      {images.length === 0 ? (
        <p>暂无图片，请上传图片</p>
      ) : (
        <div className="image-list">
          {images.map((image) => (
            <div key={image.id} className="image-item">
              <img src={image.url} alt={image.name} />
              <p style={{ fontSize: '0.8rem', wordBreak: 'break-all' }}>
                {image.name}
              </p>
              <button
                className="copy-button"
                onClick={() => copyImageUrl(image.url)}
              >
                复制链接
              </button>
              <button
                className="copy-button"
                onClick={() => copyImageUrl(getMarkdownLink(image.url))}
              >
                复制 Markdown
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default App