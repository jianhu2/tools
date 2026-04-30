# 水印服务

一个运行在服务器上的文件水印服务。客户端上传 PDF、PNG、JPG/JPEG 文件后，服务端在内存中添加文字水印，并直接返回处理后的文件，不做持久化存储。

## 功能

- 支持 PDF、PNG、JPG/JPEG。
- 支持文字水印，PDF 使用平铺水印，图片支持平铺水印和定位水印。
- 支持浏览器页面上传、预览效果后再下载。
- 支持拖动滑块调整透明度、角度、字体大小和水印间距，图片定位水印可在预览图上拖动位置。
- 上传文件和生成文件均使用内存流处理。
- 接口直接返回处理后的文件流。

## Docker Compose 生产运行

```bash
docker compose up -d --build
```

服务默认只监听服务器本机 `127.0.0.1:8000`，适合通过 SSH 隧道或 Nginx 反向代理访问。

常用管理命令：

```bash
docker compose ps
docker compose logs -f
docker compose restart
docker compose down
```

## 本地直接运行

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

如果在上级目录启动：

```bash
uvicorn watermark_service.main:app --host 0.0.0.0 --port 8000
```

默认最大上传文件大小为 `50MB`，可通过环境变量调整：

```bash
MAX_UPLOAD_MB=100 uvicorn main:app --host 0.0.0.0 --port 8000
```

如果服务器需要输出中文水印，建议安装 Noto Sans CJK 等中文字体，或通过环境变量指定字体文件：

```bash
WATERMARK_FONT_PATH=/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc uvicorn main:app --host 0.0.0.0 --port 8000
```

## 接口说明

### 健康检查

```http
GET /health
```

返回：

```json
{"status":"ok"}
```

### 添加水印

```http
POST /watermark
Content-Type: multipart/form-data
```

参数：

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| file | 是 | - | 上传文件，支持 PDF、PNG、JPG/JPEG |
| watermark_text | 是 | - | 水印文字 |
| opacity | 否 | 0.18 | 水印透明度，范围 0.01 到 1.0 |
| angle | 否 | -30 | 水印旋转角度 |
| font_size | 否 | 自动计算 | 水印字体大小 |
| gap | 否 | 160 | 平铺水印间距 |
| watermark_mode | 否 | tiled | 水印模式：`tiled` 平铺；`positioned` 定位，仅图片生效 |
| position_x | 否 | 0.5 | 定位水印横向位置，范围 0 到 1 |
| position_y | 否 | 0.5 | 定位水印纵向位置，范围 0 到 1 |
| color | 否 | #000000 | 定位水印文字颜色，CSS 十六进制格式 |

## 调用示例

PDF：

```bash
curl -X POST "http://127.0.0.1:8000/watermark" \
  -F "file=@input.pdf" \
  -F "watermark_text=内部使用" \
  -o output.pdf
```

图片：

```bash
curl -X POST "http://127.0.0.1:8000/watermark" \
  -F "file=@input.png" \
  -F "watermark_text=内部使用" \
  -F "opacity=0.2" \
  -F "angle=-30" \
  -o output.png
```

图片定位水印：

```bash
curl -X POST "http://127.0.0.1:8000/watermark" \
  -F "file=@input.png" \
  -F "watermark_text=内部使用" \
  -F "watermark_mode=positioned" \
  -F "position_x=0.8" \
  -F "position_y=0.2" \
  -F "color=#ff0000" \
  -o output.png
```

## 部署建议

生产环境建议放在 Nginx 后面，并配置：

- HTTPS。
- 上传大小限制。
- 访问鉴权。
- 请求超时限制。

服务本身不会保存上传文件或输出文件，但反向代理、访问日志或调用方可能会保存相关信息，需要按实际环境配置。
