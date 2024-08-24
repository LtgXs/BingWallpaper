# Bing Wallpaper

[EN](README.md) | [简中](README_zh-CN.md)

BingWallpaper 是一个Python脚本，用于从Bing下载每日壁纸，添加水印，设置为桌面壁纸，并将其复制到桌面。

## 功能

- 从Bing下载每日壁纸
- 添加文本和图像水印
- 设置壁纸为桌面背景
- 将壁纸复制到桌面

## 安装

1. 克隆此仓库：

   ```bash
   git clone https://github.com/LtgXs/BingWallpaper.git
   cd BingWallpaper
   ```
2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```
3. 创建并编辑配置文件 `config.json`（如果需要）：

   ```json
   {
       "idx": "0",
       "mkt": "zh-CN",
       "chk": "true",
       "ctd": "true",
       "wtm": "false",
       "wtc": 1,
       "retry_delay": 3,
       "retry_count": 10,
       "watermarks": [
           {
               "path": "watermark1.png",
               "posX": "2",
               "posY": "1.2",
               "opacity": 50 
           }
       ]
   }
   ```

## 使用

1. 运行脚本：

   ```bash
   python wallpaper.py
   ```
2. 日志文件将保存在 `APPDATA/AutoWallpaper` 目录下。

## 配置说明

- `idx`：壁纸索引，0表示当天的壁纸。
- `mkt`：市场代码，例如 `zh-CN` 表示中国。
- `chk`：是否检查当天壁纸是否已存在。
- `ctd`：是否将壁纸复制到桌面。
- `wtm`：是否添加水印。
- `wtc`：水印数量。
- `retry_delay`：下载失败后的重试延迟（秒）。
- `retry_count`：下载失败后的重试次数。
- `watermarks`：水印配置，包括路径、位置和透明度。

## 贡献

欢迎提交问题和拉取请求！

## 许可证

此项目使用 MIT 许可证。
