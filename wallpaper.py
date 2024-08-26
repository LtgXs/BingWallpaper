import os
import requests
import json
from datetime import datetime
import ctypes
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import time
import subprocess

CONFIG_PATH = 'config.json'
DEFAULT_CONFIG = {
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
    ],
    "post_execution_apps": []
}

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
    elif key in ["wtc", "retry_delay", "retry_count"]:
        return isinstance(value, int) and value > 0
    elif key == "watermarks":
        for wm in value:
            if not all(k in wm for k in ["path", "posX", "posY", "opacity"]):
                return False
            if not (isinstance(wm.get("opacity", 50), int) and 0 <= wm["opacity"] <= 100):
                return False
        return True
    elif key == "post_execution_apps":
        return isinstance(value, list) and all(isinstance(app, str) for app in value)
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

def add_watermark(image_path, watermarks, wtc, watermark_file, log_file):
    try:
        base_image = Image.open(image_path)
        draw = ImageDraw.Draw(base_image)
        font = ImageFont.truetype("arial.ttf", 46)
        text = "   Auto Change Wallpaper By LtqX\nPictures all from and belong to bing"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        textwidth, textheight = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        width, height = base_image.size
        x = (width - textwidth) / 2
        y = height - textheight - int(height * 0.10)
        draw.text((x, y), text, font=font, fill=(128, 128, 128, 204))
        
        for i in range(min(wtc, len(watermarks))):
            wm = watermarks[i]
            watermark_path = wm.get('path', watermark_file)
            posX = float(wm.get('posX', '2'))
            posY = float(wm.get('posY', '1.2'))
            opacity = wm.get('opacity', 50) / 100
            try:
                watermark = Image.open(watermark_path).convert("RGBA")
                watermark = watermark.resize((int(base_image.width / 5), int(base_image.height / 5)))
                alpha = watermark.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
                watermark.putalpha(alpha)
                base_image.paste(watermark, (int(base_image.width / posX), int(base_image.height / posY)), watermark)
                log_message(f'Watermark {i+1} added successfully at position ({posX}, {posY}) with opacity {opacity*100}%', log_file)
            except FileNotFoundError:
                log_message(f'Watermark {i+1} file not found: {watermark_path}', log_file)
            except Exception as e:
                log_message(f'Failed to add watermark {i+1}: {e}', log_file)
        
        base_image.save(image_path, quality=95)
    except Exception as e:
        log_message(f'Failed to add watermark: {e}', log_file)

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

    log_message('\n********************Log Start********************', log_file)
    config = load_config(log_file)
    idx = config['idx']
    mkt = config['mkt']
    chk = config['chk']
    ctd = config['ctd']
    wtm = config['wtm']
    wtc = int(config['wtc'])
    retry_delay = config['retry_delay']
    retry_count = config['retry_count']
    watermarks = config['watermarks']
    post_execution_apps = config['post_execution_apps']
    
    watermark_details = ', '.join([f'Watermark {i+1}: path={wm["path"]}, posX={wm["posX"]}, posY={wm["posY"]}' for i, wm in enumerate(watermarks)])
    log_message(f'Config values: idx={idx}, mkt={mkt}, chk={chk}, ctd={ctd}, wtm={wtm}, wtc={wtc}, retry_delay={retry_delay}, retry_count={retry_count}, {watermark_details}, post_execution_apps={post_execution_apps}', log_file)

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
            add_watermark(image_path, watermarks, wtc, watermark_file, log_file)

        set_wallpaper(image_path, log_file)

        if ctd == 'true':
            copy_to_desktop(image_path, log_file)

        run_post_execution_apps(post_execution_apps, log_file)

    finally:
        log_message('*********************Log End*********************', log_file)

if __name__ == "__main__":
    main()
