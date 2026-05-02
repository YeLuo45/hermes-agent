---
name: local-image-read
description: 读取本地图片文件并使用视觉AI分析
trigger: 用户要求读取、分析、或描述本地图片文件内容
---

# Local Image Read

读取本地图片文件并使用视觉AI分析。

## 核心流程

### 1. 先检查图片基本信息

```python
python3 -c "
from PIL import Image
path = '/home/hermes/.hermes/images/clip_20260502_180019_1.png'
img = Image.open(path)
print(f'Path: {path}')
print(f'Size: {img.size}')
print(f'Mode: {img.mode}')
"
```

### 2. 获取 base64 编码（用于调试或手动分析）

```python
python3 -c "
import base64
path = '/home/hermes/.hermes/images/clip_20260502_180019_1.png'
with open(path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')
print(f'Base64 length: {len(b64)}')
# 只打印前500字符用于调试
print(b64[:500])
"
```

### 3. 通过 vision_analyze 分析

由于 vision_analyze 对本地文件支持不稳定，建议：
- 优先用浏览器打开截图确认内容
- 或将图片上传到可访问的 URL

## 已知限制

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| vision_analyze 返回错误引导文本 | 环境限制 | 直接询问用户图片内容 |
| tesseract OCR 无法安装 | 缺少系统权限 | 使用 vision_analyze 或让用户描述 |
| browser_navigate 加载本地文件失败 | file:// 协议问题 | 用其他方式读取 |

## 验证命令

```bash
python3 -c "
from PIL import Image
img = Image.open('/home/hermes/.hermes/images/clip_20260502_180019_1.png')
print(f'OK: {img.size} {img.mode}')
"
```

期望输出: `OK: (575, 387) RGBA`
