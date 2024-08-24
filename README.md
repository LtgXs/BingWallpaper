# Auto Change Wallpaper

[EN](README.md) | [简中](README_zh-CN.md)

Auto Change Wallpaper is a Python script that downloads daily wallpapers from Bing, adds watermarks, sets them as desktop wallpapers, and copies them to the desktop.

## Features

- Download daily wallpapers from Bing
- Add text and image watermarks
- Set wallpaper as desktop background
- Copy wallpaper to desktop

## Installation

1. Clone this repository:
    ```bash
    git clone https://github.com/LtgXs/BingWallpaper.git
    cd AutoChangeWallpaper
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Create and edit the `config.json` file (if needed):
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

## Usage

1. Run the script:
    ```bash
    python wallpaper.py
    ```

2. Log files will be saved in the `APPDATA/AutoWallpaper` directory.

## Configuration

- `idx`: Wallpaper index, 0 for today's wallpaper.
- `mkt`: Market code, e.g., `zh-CN` for China.
- `chk`: Check if today's wallpaper already exists.
- `ctd`: Copy wallpaper to desktop.
- `wtm`: Add watermark.
- `wtc`: Number of watermarks.
- `retry_delay`: Retry delay in seconds.
- `retry_count`: Number of retry attempts.
- `watermarks`: Watermark configuration, including path, position, and opacity.

## Contributing

Contributions are welcome! Feel free to submit issues and pull requests.

## License

This project is licensed under the MIT License.
