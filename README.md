# Tools

这个仓库用于集中管理一些独立的小工具服务。每个工具使用独立目录维护，方便后续扩展、部署和单独迭代。

## 项目结构

```text
.
├── watermark_service/          # 文件水印服务
│   ├── Dockerfile
│   ├── README.md
│   ├── docker-compose.yml
│   ├── main.py
│   └── requirements.txt
└── clean_watermark_service/    # 预留：后续去水印工具
```

## 当前工具

### watermark_service

文件水印服务，支持上传 PDF、PNG、JPG/JPEG 文件并添加文字水印。

主要功能：

- PDF 使用平铺文字水印。
- 图片支持平铺水印和定位水印。
- 定位水印支持轻量角标、四角快捷位置、拖动微调、自动反差颜色。
- 浏览器页面上传、预览、确认后下载。
- 服务端仅在内存中处理文件，不持久化保存原文件或结果文件。
- 支持 Docker Compose 部署。

运行和接口说明见：[`watermark_service/README.md`](watermark_service/README.md)。

## 后续工具规划

后续新增工具时，建议按独立目录放在仓库根目录下，例如：

```text
clean_watermark_service/
image_convert_service/
pdf_tools_service/
```

每个工具目录内维护自己的 `README.md`、依赖文件和部署配置。