import os
import shutil
import requests
import json
from datetime import datetime, timedelta
import ctypes
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import time
import subprocess

CONFIG_PATH = 'config.json'
ARCHIVE_DAYS = 10
ARCHIVE_PATH = os.path.join(os.getenv('APPDATA'), 'AutoWallpaper', 'Archive')
DEFAULT_CONFIG = {
    "idx": 0,
    "mkt": "zh-CN",
    "chk": "true",
    "ctd": "true",
    "wtm": "false",
    "retry_delay": 3,
    "retry_count": 10,
    "watermarks": [
        {
            "type": "image",
            "path": "watermark1.png",
            "posX": 2,
            "posY": 1.2,
            "opacity": 50
        },
        {
            "type": "text",
            "content": "Sample Text Watermark",
            "posX": 2,
            "posY": 1.5,
            "opacity": 75,
            "font_type": "arial.ttf",
            "font_size": 46,
            "font_color": [128, 128, 128, 192],
            "font_weight": "normal"
        }
    ],
    "post_execution_apps": [],
    "copy_to_paths": []
}

def archive_old_folders(base_folder, archive_folder, log_file, days=30):
    if not os.path.exists(archive_folder):
        os.makedirs(archive_folder)
    cutoff_date = datetime.now() - timedelta(days=days)
    for folder_name in os.listdir(base_folder):
        folder_path = os.path.join(base_folder, folder_name)
        if os.path.isdir(folder_path):
            try:
                folder_date = datetime.strptime(folder_name, '%Y.%m.%d')
                if folder_date < cutoff_date:
                    year_folder = os.path.join(archive_folder, str(folder_date.year))
                    if not os.path.exists(year_folder):
                        os.makedirs(year_folder)
                    shutil.move(folder_path, os.path.join(year_folder, folder_name))
                    log_message(f'Archived folder {folder_name} to {year_folder}', log_file)
            except ValueError:
                print(f'Skipped folder {folder_name} (not in yyyy.mm.dd format)')

def load_config(log_file):
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            for key, default_value in DEFAULT_CONFIG.items():
                if key in user_config:
                    if validate_config_value(key, user_config[key]):
                        config[key] = user_config[key]
                    else:
                        log_message(f'Invalid value for {key}: {user_config[key]}. Resetting to default value.', log_file)
                else:
                    log_message(f'Missing key {key}. Resetting to default value.', log_file)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except (json.JSONDecodeError, ValueError) as e:
            log_message(f'Error loading config: {e}. Resetting invalid entries to default values.', log_file)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
    else:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    return config

def validate_config_value(key, value):
    if key in ["chk", "ctd", "wtm"]:
        return value in ["true", "false"]
    elif key in ["retry_delay", "retry_count"]:
        return isinstance(value, int) and value > 0
    elif key == "watermarks":
        for wm in value:
            if "type" not in wm or wm["type"] not in ["image", "text"]:
                return False
            if not all(k in wm for k in ["posX", "posY", "opacity"]):
                return False
            if wm["type"] == "image":
                if "path" not in wm or not isinstance(wm["path"], str):
                    return False
            elif wm["type"] == "text":
                if "content" not in wm or not isinstance(wm["content"], str):
                    return False
                if "font_type" in wm and not isinstance(wm["font_type"], str):
                    return False
                if "font_size" in wm and not isinstance(wm["font_size"], int):
                    return False
                if "font_color" in wm:
                    if not (isinstance(wm["font_color"], list) and len(wm["font_color"]) == 4 and all(isinstance(c, int) for c in wm["font_color"])):
                        return False
                if "font_weight" in wm and wm["font_weight"] not in ["normal", "bold", "light"]:
                    return False
            if not (isinstance(wm.get("opacity", 50), int) and 0 <= wm["opacity"] <= 100):
                return False
        return True
    elif key == "post_execution_apps" or key == "copy_to_paths":
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    return True

def log_message(message, log_file):
    global log_initialized
    if not log_initialized:
        if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
            with open(log_file, 'a', encoding='utf-8') as log:
                log.write('\n')
        log_initialized = True
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {message}\n')

def download_file(url, path, log_file, retry_delay, retry_count):
    for attempt in range(retry_count):
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(path, 'wb') as file:
                file.write(response.content)
            log_message(f'Successfully downloaded {url}', log_file)
            return True
        except requests.exceptions.RequestException as e:
            log_message(f'Failed to download {url} (attempt {attempt + 1}/{retry_count}): {e}', log_file)
            if attempt < retry_count - 1:
                time.sleep(retry_delay)
    log_message(f'Failed to download {url} after {retry_count} attempts', log_file)
    return False

def add_watermark(image_path, watermarks, watermark_file, log_file):
    try:
        base_image = Image.open(image_path).convert("RGBA")
        default_font = ImageFont.truetype("BRADHITC.TTF", 62)
        copyright_text = "   Auto Change Wallpaper By LtqX\n\nPictures all from and belong to Bing"
        add_text_watermark(base_image, copyright_text, default_font, (128, 128, 128, 204), 2, 1.2, 1, font_weight='bold')
        for i, wm in enumerate(watermarks):
            posX = float(wm.get('posX', '2'))
            posY = float(wm.get('posY', '1.2'))
            opacity = wm.get('opacity', 50) / 100
            
            if wm["type"] == "image":
                add_image_watermark(base_image, wm, watermark_file, posX, posY, opacity, log_file, i)
            elif wm["type"] == "text":
                add_text_watermark(base_image, wm['content'], ImageFont.truetype(wm.get('font_type', 'arial.ttf'), wm.get('font_size', 46)), 
                                   tuple(wm.get('font_color', [128, 128, 128, 255])), posX, posY, opacity, wm.get('font_weight', 'normal'), log_file, i)
        base_image.convert("RGB").save(image_path, quality=98)
    except Exception as e:
        log_message(f'Failed to add watermark: {e}', log_file)

def add_text_watermark(base_image, text, font, color, posX, posY, opacity, font_weight='normal', log_file=None, index=None):
    draw = ImageDraw.Draw(base_image)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    textwidth, textheight = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    x = (base_image.width - textwidth) / posX
    y = (base_image.height - textheight) / posY
    
    text_layer = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    text_draw = ImageDraw.Draw(text_layer)
    
    if font_weight == 'bold':
        draw_bold_text(text_draw, (x, y), text, font, tuple(color[:3]) + (int(color[3] * opacity),), boldness=1)
    elif font_weight == 'thin':
        draw_thin_text(text_draw, (x, y), text, font, tuple(color[:3]) + (int(color[3] * opacity),))
    else:
        text_draw.text((x, y), text, font=font, fill=tuple(color[:3]) + (int(color[3] * opacity),))
    
    base_image.alpha_composite(text_layer)
    
    if log_file and index is not None:
        log_message(f'Text watermark {index+1} added successfully at position ({posX}, {posY}) with opacity {opacity*100}%', log_file)

def add_image_watermark(base_image, wm, watermark_file, posX, posY, opacity, log_file, index):
    watermark_path = wm.get('path', watermark_file)
    try:
        watermark = Image.open(watermark_path).convert("RGBA")
        watermark = watermark.resize((int(base_image.width / 5), int(base_image.height / 5)))
        alpha = watermark.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        watermark.putalpha(alpha)
        base_image.paste(watermark, (int(base_image.width / posX), int(base_image.height / posY)), watermark)
        log_message(f'Watermark {index+1} added successfully at position ({posX}, {posY}) with opacity {opacity*100}%', log_file)
    except FileNotFoundError:
        log_message(f'Watermark {index+1} file not found: {watermark_path}', log_file)
    except Exception as e:
        log_message(f'Failed to add watermark {index+1}: {e}', log_file)

def draw_thin_text(draw, position, text, font, fill):
    x, y = position
    draw.text((x, y), text, font=font, fill=fill)
    image = draw.im.filter(ImageFilter.GaussianBlur(1))
    return image

def draw_bold_text(draw, position, text, font, fill, boldness=1):
    x, y = position
    for offset in range(-boldness, boldness + 1):
        draw.text((x + offset, y), text, font=font, fill=fill)
        draw.text((x, y + offset), text, font=font, fill=fill)
    return draw

def set_wallpaper(image_path, log_file):
    SPI_SETDESKWALLPAPER = 20
    result = ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
    if result:
        log_message('Wallpaper changed successfully', log_file)
    else:
        log_message('Failed to change wallpaper', log_file)

def copy_to_desktop(image_path, log_file):
    try:
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'wallpaper.jpg')
        with open(image_path, 'rb') as src, open(desktop_path, 'wb') as dst:
            dst.write(src.read())
        log_message('Wallpaper copied to desktop successfully', log_file)
    except Exception as e:
        log_message(f'Failed to copy wallpaper to desktop: {e}', log_file)

def expand_environment_variables(path):
    return os.path.expandvars(path)
def run_post_execution_apps(apps, log_file):
    for app in apps:
        app_path = expand_environment_variables(app)
        log_message(f'Trying to execute {app_path}', log_file)
        try:
            result = subprocess.run(app_path, check=True)
            log_message(f'Successfully executed {app_path} with return code {result.returncode}', log_file)
        except subprocess.CalledProcessError as e:
            log_message(f'Failed to execute {app_path}: {e}', log_file)
        except Exception as e:
            log_message(f'Unexpected error while executing {app_path}: {e}', log_file)

def main():
    global log_initialized
    log_initialized = False
    name = datetime.now().strftime('%Y.%m.%d')
    bing_api = 'https://www.bing.com/HPImageArchive.aspx?n=1'
    folder = os.path.join(os.getenv('APPDATA'), 'AutoWallpaper')
    dfolder = os.path.join(folder, name)
    watermark_file = os.path.join(folder, 'watermark.png')
    os.makedirs(dfolder, exist_ok=True)
    log_file = os.path.join(dfolder, f'{name}.log')

    log_message('********************Log Start********************', log_file)
    archive_old_folders(folder, ARCHIVE_PATH, log_file, ARCHIVE_DAYS)
    config = load_config(log_file)
    idx = config['idx']
    mkt = config['mkt']
    chk = config['chk']
    ctd = config['ctd']
    wtm = config['wtm']
    retry_delay = config['retry_delay']
    retry_count = config['retry_count']
    watermarks = config['watermarks']
    post_execution_apps = config['post_execution_apps']
    copy_to_paths = config.get('copy_to_paths', [])

    watermark_details = ', '.join([
        f'Watermark {i+1}: type={wm["type"]}, ' +
        (f'path={wm["path"]}, ' if wm["type"] == "image" else f'content={wm["content"]}, ') +
        f'posX={wm["posX"]}, posY={wm["posY"]}, opacity={wm["opacity"]}'
        for i, wm in enumerate(watermarks)
    ])
    log_message(f'Config values: idx={idx}, mkt={mkt}, chk={chk}, ctd={ctd}, wtm={wtm}, retry_delay={retry_delay}, retry_count={retry_count}, {watermark_details}, post_execution_apps={post_execution_apps}, copy_to_paths={copy_to_paths}', log_file)

    try:
        if chk == 'true' and os.path.exists(os.path.join(dfolder, f'{name}.jpg')):
            log_message("Today's wallpaper already existed", log_file)
            return

        api_url = f'{bing_api}&mkt={mkt}&idx={idx}'
        api_json_path = os.path.join(dfolder, 'api.json')

        if not download_file(f'{api_url}&format=js', api_json_path, log_file, retry_delay, retry_count):
            log_message('Failed to download API files', log_file)
            return

        link = None
        with open(api_json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            link = data['images'][0]['urlbase']

        if not link:
            log_message('Failed to parse download link from API response', log_file)
            return

        full_link = f'https://www.bing.com{link}_UHD.jpg'
        image_path = os.path.join(dfolder, f'{name}.jpg')
        if not download_file(full_link, image_path, log_file, retry_delay, retry_count):
            log_message('Failed to download image', log_file)
            return

        if wtm == 'true':
            original_image_path = os.path.join(dfolder, f'{name}_original.jpg')
            shutil.copy(image_path, original_image_path)
            log_message(f'Original image saved as {original_image_path}', log_file)
            add_watermark(image_path, watermarks, watermark_file, log_file)

        for path in copy_to_paths:
            try:
                expanded_path = os.path.expandvars(path)
                if os.path.splitext(expanded_path)[1]:
                    target_path = expanded_path
                else:
                    os.makedirs(expanded_path, exist_ok=True)
                    target_path = os.path.join(expanded_path, f'{name}.jpg')
                shutil.copy(image_path, target_path)
                log_message(f'Image copied to {target_path}', log_file)
            except Exception as e:
                log_message(f'Failed to copy image to {expanded_path}: {e}', log_file)

        set_wallpaper(image_path, log_file)

        if ctd == 'true':
            copy_to_desktop(image_path, log_file)

        run_post_execution_apps(post_execution_apps, log_file)

    finally:
        log_message('*********************Log End*********************', log_file)

if __name__ == "__main__":
    main()
