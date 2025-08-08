import json
import math
import random
import io
import re
from math import ceil, sqrt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Literal

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.sv import SV, get_plugin_available_prefix
from gsuid_core.data_store import get_res_path
from gsuid_core.utils.image.convert import convert_img

# Attempt to import resources from WutheringWavesUID, with a fallback
try:
    from ....WutheringWavesUID.WutheringWavesUID.utils.fonts.waves_fonts import (
        waves_font_18, waves_font_20,
        waves_font_28, waves_font_30, waves_font_36,
    )
    from ....WutheringWavesUID.WutheringWavesUID.utils.image import get_attribute_prop, get_footer
    PREFIX = get_plugin_available_prefix("TodayEcho")
except ImportError:
    logger.warning("Could not load resources from WutheringWavesUID, using defaults.")
    def create_font(size):
        try:
            return ImageFont.truetype("msyh.ttc", size)
        except IOError:
            return ImageFont.load_default()
    waves_font_18, waves_font_20, waves_font_28, waves_font_30, waves_font_36 = [create_font(s) for s in [18, 20, 24, 28, 30, 36]]
    async def get_attribute_prop(icon_name: str):
        raise FileNotFoundError(f"Icon {icon_name} not found.")
    def get_footer(color: Literal["white", "black", "hakush"] = "white"):
        raise FileNotFoundError(f"Footer image not found.")
    PREFIX = ""

# --- Service Definitions ---
sv_gacha_phantom_history = SV("鸣潮声骸历史", priority=5)
sv_gacha_phantom_action = SV("鸣潮声骸抽取", priority=6)


# --- Path Configuration ---
PLUGIN_PATH = Path(__file__).parent.parent
DATA_PATH = get_res_path() / "TodayEcho"
DATA_PATH.mkdir(exist_ok=True)
CONFIG_FILE = PLUGIN_PATH / "todayecho_echo" / "phantom_substats_config.json"
TEXT_PATH = PLUGIN_PATH / "todayecho_help" / "icon_path"
TUNER_ICON_PATH = TEXT_PATH / "梭哈.png"

# --- Color Definitions (Wuthering Waves Themed) ---
ACCENT_GOLD = (255, 223, 128)
ACCENT_RED = (255, 80, 80)
WHITE = (240, 240, 240)
GREY = (160, 160, 160)
BG_COLOR = (28, 32, 36, 255)       # Main background for image combining
CARD_GRADIENT_START = (15, 18, 22) # Card background gradient start
CARD_GRADIENT_END = (30, 35, 45)   # Card background gradient end
PANEL_BG = (20, 22, 26, 180)       # Semi-transparent panel backgrounds
SEPARATOR_TEAL = (60, 150, 170, 200) # Divider line color

class PhantomStat:
    """Represents a substat on a Wuthering Waves Echo."""
    def __init__(self, name: str, icon: str, value: float, is_percent: bool, is_max: bool = False):
        self.name, self.icon, self.value = name, icon, value
        self.is_percent, self.is_max = is_percent, is_max
        
    @property
    def display_value(self) -> str:
        return f"{self.value}%" if self.is_percent else str(int(self.value))

    def to_dict(self) -> Dict:
        return {
            "name": self.name, "icon": self.icon, "value": self.value,
            "is_percent": self.is_percent, "is_max": self.is_max,
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)

# --- Data Handling Functions (Unchanged) ---
def load_config() -> Dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        default_config = {
            "substats": [
            {"name": "攻击", "icon": "攻击", "values": [50, 40, 30], "is_percent": False},
            {"name": "攻击", "icon": "攻击", "values": [11.6, 10.9, 10.1, 9.4, 8.6, 7.9, 7.1, 6.4], "is_percent": True},
            {"name": "生命", "icon": "生命", "values": [580, 540, 510, 470, 430, 390, 360, 320], "is_percent": False},
            {"name": "生命", "icon": "生命", "values": [11.6, 10.9, 10.1, 9.4, 8.6, 7.9, 7.1, 6.4], "is_percent": True},
            {"name": "防御", "icon": "防御", "values": [60, 50, 40], "is_percent": False},
            {"name": "防御", "icon": "防御", "values": [14.7, 13.8, 12.8, 11.8, 10.9, 10.0, 9.0, 8.1], "is_percent": True},
            {"name": "暴击", "icon": "暴击", "values": [10.5, 9.9, 9.3, 8.7, 8.1, 7.5, 6.9, 6.3], "is_percent": True},
            {"name": "暴击伤害", "icon": "暴击伤害", "values": [21.0, 19.8, 18.6, 17.4, 16.2, 15.0, 13.8, 12.6], "is_percent": True},
            {"name": "共鸣效率", "icon": "共鸣效率", "values": [11.6, 10.9, 10.1, 9.4, 8.6, 7.9, 7.1, 6.4], "is_percent": True},
            {"name": "普攻伤害加成", "icon": "普攻伤害加成", "values": [11.6, 10.9, 10.1, 9.4, 8.6, 7.9, 7.1, 6.4], "is_percent": True},
            {"name": "重击伤害加成", "icon": "重击伤害加成", "values": [11.6, 10.9, 10.1, 9.4, 8.6, 7.9, 7.1, 6.4], "is_percent": True},
            {"name": "共鸣技能伤害加成", "icon": "共鸣技能伤害加成", "values": [11.6, 10.9, 10.1, 9.4, 8.6, 7.9, 7.1, 6.4], "is_percent": True},
            {"name": "共鸣解放伤害加成", "icon": "共鸣解放伤害加成", "values": [11.6, 10.9, 10.1, 9.4, 8.6, 7.9, 7.1, 6.4], "is_percent": True}
            ],
            "settings": {
            "daily_limit": 20,
            "white_list": [
                "644572093"
            ],
            "stats_count": 5,
            "max_value_color": [
                255,
                60,
                60
            ],
            "normal_color": [
                255,
                255,
                255
            ]
            }
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        return default_config

def load_records(user_id: str) -> Dict:
    if (DATA_PATH / f'{user_id}.json').exists():
        with open(DATA_PATH / f'{user_id}.json', 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_records(user_id: str, records: Dict):
    with open(DATA_PATH / f'{user_id}.json', 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def generate_phantom_stats(config: Dict) -> List[PhantomStat]:
    substats = config["substats"]
    stats_count = config["settings"]["stats_count"]
    num_to_sample = min(stats_count, len(substats))
    selected_configs = random.sample(substats, num_to_sample)
    
    stats = []
    for stat_config in selected_configs:
        value = random.choice(stat_config["values"])
        is_max = (value == max(stat_config["values"]))
        stats.append(PhantomStat(
            name=stat_config["name"], icon=stat_config["icon"], value=value,
            is_percent=stat_config["is_percent"], is_max=is_max
        ))
    return stats


async def draw_single_result_card(
    stats: List[PhantomStat], roll_number: int
) -> Image.Image:
    """Draws a single, aesthetically enhanced result card."""
    width, height = 540, 680
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    
    # Create a smoother, darker background gradient
    gradient = Image.new("RGBA", (width, height))
    draw_gradient = ImageDraw.Draw(gradient)
    for i in range(height):
        r, g, b = [int(start + (end - start) * i / height) for start, end in zip(CARD_GRADIENT_START, CARD_GRADIENT_END)]
        draw_gradient.rectangle([0, i, width, i + 1], fill=(r, g, b, 255))
    
    img.alpha_composite(gradient.filter(ImageFilter.GaussianBlur(radius=3)))
    draw = ImageDraw.Draw(img)
    
    # Title Area
    title_bg_y_start = 20
    title_bg_height = 80
    title_bg = Image.new("RGBA", (width - 40, title_bg_height), (0, 0, 0, 0))
    ImageDraw.Draw(title_bg).rounded_rectangle(
        [0, 0, width - 40, title_bg_height], radius=15, fill=PANEL_BG
    )
    img.alpha_composite(title_bg, (20, title_bg_y_start))
    
    title_text = f"第 {roll_number} 次梭哈结果"
    draw.text(
        (width // 2, title_bg_y_start + title_bg_height // 2),
        title_text, fill=ACCENT_GOLD, font=waves_font_36, anchor="mm"
    )
    
    # Stats Area
    content_y_start = title_bg_y_start + title_bg_height + 20
    content_height = 530
    content_bg = Image.new("RGBA", (width - 60, content_height), (0, 0, 0, 0))
    ImageDraw.Draw(content_bg).rounded_rectangle(
        [0, 0, width - 60, content_height], radius=20, fill=PANEL_BG
    )
    img.alpha_composite(content_bg, (30, content_y_start))
    
    line_height = 95
    base_y = content_y_start + 40
    
    for i, stat in enumerate(stats):
        y_pos = base_y + i * line_height
        
        # Separator line with accent color
        if i > 0:
            separator_y = y_pos - (line_height // 2) + 5
            draw.line(
                [(60, separator_y), (width - 60, separator_y)],
                fill=SEPARATOR_TEAL, width=1
            )
            
        # Icon
        try:
            prop_img = await get_attribute_prop(stat.icon)
            img.alpha_composite(prop_img.resize((50, 50)), (70, y_pos))
        except Exception as e:
            logger.warning(f"Could not load icon {stat.icon}: {e}")
            placeholder = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
            ImageDraw.Draw(placeholder).ellipse([5, 5, 45, 45], fill=(80, 80, 80, 150))
            img.alpha_composite(placeholder, (70, y_pos))
        
        # Stat Name
        is_double_crit = stat.name in ["暴击", "暴击伤害"]

        if stat.is_max or is_double_crit:
            text_color = ACCENT_GOLD
        else:
            text_color = WHITE
        name_x = 140
        draw.text(
            (name_x, y_pos + 25), stat.name, fill=text_color,
            font=waves_font_28, anchor="lm"
        )
        
        # Stat Value
        value_x = width - 70
        draw.text(
            (value_x, y_pos + 25), stat.display_value, fill=text_color,
            font=waves_font_30, anchor="rm"
        )
        
        # --- MODIFICATION START ---
        # MAX Tag is now drawn ABOVE the stat name
        if stat.is_max:
            # 1. Calculate the width of the stat name to find its horizontal center
            name_width = draw.textlength(stat.name, font=waves_font_28)
            tag_center_x = name_x + (name_width / 2)
            
            # 2. Define the Y position: a few pixels above the icon's top edge
            tag_y = y_pos - 5
            
            # 3. To color text differently, we must draw them separately.
            # We calculate the total width of the tag to center it manually.
            tag_font = waves_font_18
            star_text = "★ "  # Add a space for better visual separation
            max_text = "MAX"
            
            star_width = draw.textlength(star_text, font=tag_font)
            max_width = draw.textlength(max_text, font=tag_font)
            total_tag_width = star_width + max_width
            
            # 4. Calculate the starting X position for the combined tag
            tag_start_x = tag_center_x - (total_tag_width / 2)
            
            # 5. Draw the "★" in red
            draw.text(
                (tag_start_x, tag_y), star_text, fill=ACCENT_RED,
                font=tag_font, anchor="lt"  # Anchor left-top
            )
            # 6. Draw the "MAX" in gold, right next to the star
            draw.text(
                (tag_start_x + star_width, tag_y), max_text, fill=ACCENT_RED,
                font=tag_font, anchor="lt"  # Anchor left-top
            )
        # --- MODIFICATION END ---
            
    return img


async def add_footer(base_img: Image.Image, user_name: str, tuners_remaining: int) -> Image.Image:
    """
    Adds a footer with user info and a decoration bar.
    """
    base_w, base_h = base_img.size
    text_area_height = 85
    
    bar_to_paste = None
    deco_bar_height = 0

    try:
        footer_deco_bar = get_footer()
        
        # --- NEW LOGIC: Scaling and Sizing ---
        if footer_deco_bar.width > base_w:
            # Condition 1: Bar is wider than the base image -> Scale it down
            ratio = base_w / footer_deco_bar.width  # Get scaling ratio (< 1.0)
            new_deco_h = int(footer_deco_bar.height * ratio)
            bar_to_paste = footer_deco_bar.resize((base_w, new_deco_h), Image.Resampling.LANCZOS)
        else:
            # Condition 2: Bar is narrower or equal -> Use original
            bar_to_paste = footer_deco_bar
        
        deco_bar_height = bar_to_paste.height

    except Exception as e:
        logger.warning(f"Could not load footer decoration bar: {e}. Using a fallback solid bar.")
        bar_to_paste = None
        deco_bar_height = 20  # Fallback height for the solid bar

    # --- Image Canvas Creation (uses the calculated deco_bar_height) ---
    new_height = base_h + text_area_height + deco_bar_height
    final_img = Image.new("RGBA", (base_w, new_height), BG_COLOR)
    final_img.paste(base_img, (0, 0))
    draw = ImageDraw.Draw(final_img)
    
    # --- Text and Info Drawing (Unchanged) ---
    footer_y_start = base_h
    user_name = user_name if len(user_name) <= 8 else user_name[:7] + "..."
    draw.text((30, footer_y_start + 25), f"{user_name}", fill=WHITE, font=waves_font_28, anchor="lm")
    draw.text((30, footer_y_start + 60), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fill=GREY, font=waves_font_20, anchor="lm")
    
    # --- MODIFIED: 调谐器图标在数量右边 ---
    tuner_text = f"剩余: {tuners_remaining * 50}"
    tuner_font = waves_font_28
    tuner_text_width = draw.textlength(tuner_text, font=tuner_font)
    icon_size, padding = 36, 8  # 减少padding
    text_y_pos = footer_y_start + text_area_height / 2
    
    # 先绘制文字（从右边往左算位置）
    text_x_pos = base_w - 30 - icon_size - padding  # 为图标和间距留空间
    draw.text((text_x_pos, text_y_pos), tuner_text, fill=WHITE, font=tuner_font, anchor="rm")
    
    # 再绘制图标（在文字右边）
    try:
        tuner_icon = Image.open(TUNER_ICON_PATH).convert("RGBA").resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        icon_x_pos = text_x_pos + padding  # 在文字右边
        icon_y_pos = int(footer_y_start + (text_area_height - icon_size) / 2)
        final_img.alpha_composite(tuner_icon, (icon_x_pos, icon_y_pos))
    except Exception as e:
        logger.warning(f"Could not load tuner icon: {e}")
    
    # --- NEW LOGIC: Centered Pasting ---
    deco_bar_y_start = base_h + text_area_height
    if bar_to_paste:
        # Calculate X position to center the bar
        deco_x_pos = (base_w - bar_to_paste.width) // 2
        final_img.paste(bar_to_paste, (deco_x_pos, deco_bar_y_start), bar_to_paste)
    else:
        # Fallback solid color bar (already full-width)
        draw.rectangle([0, deco_bar_y_start, base_w, new_height], fill=SEPARATOR_TEAL)
        
    return final_img


async def combine_images(images: List[Image.Image]) -> Image.Image:
    """
    将多张图片拼接成一张大图
    """
    num_images = len(images)
    if not images: return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    if num_images == 1: return images[0]

    single_w, single_h = images[0].size
    padding = 20
    
    cols = int(math.ceil(math.sqrt(num_images)))
    rows = int(math.ceil(num_images / cols))
    
    total_w = cols * single_w + (cols + 1) * padding
    total_h = rows * single_h + (rows + 1) * padding
    
    combined_img = Image.new("RGBA", (total_w, total_h), BG_COLOR)
    
    for i, img in enumerate(images):
        row, col = divmod(i, cols)
        x = col * (single_w + padding) + padding
        y = row * (single_h + padding) + padding
        combined_img.paste(img, (x, y))
            
    return combined_img


@sv_gacha_phantom_action.on_command(('梭哈', '重新梭哈'))
async def gacha_phantom_command(bot: Bot, ev: Event):
    """Performs one or more Echo gacha rolls. Format: 梭哈 [number]"""
    user_id, user_name = str(ev.user_id), ev.sender.get("nickname", "Player")
    config = load_config()
    limit = config["settings"].get("daily_limit", 20)
    if user_id in config["settings"].get("white_list", []):
        limit = math.inf
    if "列表" in ev.text or "结果" in ev.text:
        return
    cn_num_map = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, \
        '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15, '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20, \
        '两': 2, '俩': 2, "①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5, "⑥": 6, "⑦": 7, "⑧": 8, "⑨": 9, "⑩": 10}
    for key, value in cn_num_map.items():
        ev.text = ev.text.replace(key, str(value))
    match = re.search(r'(\d+)', ev.text)
    roll_count = int(match.group(1)) if match and int(match.group(1)) > 0 else 1
    if (not match or roll_count < 1) and random.random() < 0.2: # 20%概率触发帮助
        await bot.send(" 梭哈可以跟随次数，如：梭哈5次", at_sender=True)

    all_records = load_records(user_id)
    today_str = datetime.now().strftime('%Y-%m-%d')
    records_today = all_records.get(today_str, {})
    user_daily_results = records_today.get(user_id, [])
    all_records = {today_str: records_today}
    
    rolls_done = len(user_daily_results)
    rolls_remaining = limit - rolls_done
    
    if rolls_remaining <= 0:
        return await bot.send(f" 你今天的调谐器已经用完啦！", at_sender=True)
    if roll_count > rolls_remaining:
        return await bot.send(f" 你的调谐器不足！剩余调谐器 {rolls_remaining * 50}！", at_sender=True)

    new_stats_records, image_objects = [], []
    try:
        for i in range(roll_count):
            stats = generate_phantom_stats(config)
            new_stats_records.append([s.to_dict() for s in stats])
            
            img = await draw_single_result_card(stats, roll_number=rolls_done + i + 1)
            image_objects.append(img)
        
        # Save records
        records_today.setdefault(user_id, []).extend(new_stats_records)
        all_records[today_str] = records_today
        save_records(user_id, all_records)
        
        final_tuners_remaining = rolls_remaining - roll_count

        # Combine images and add footer
        if len(image_objects) == 1:
            final_img = await add_footer(image_objects[0], user_name, final_tuners_remaining)
        else:
            combined_img = await combine_images(image_objects)
            final_img = await add_footer(combined_img, user_name, final_tuners_remaining)
            
        final_img_bytes = await convert_img(final_img)
        await bot.send(final_img_bytes)
        
        logger.info(f"User {user_id}({user_name}) performed {roll_count} roll(s)")
    except Exception as e:
        logger.exception(f"Failed to process Echo roll: {e}")


@sv_gacha_phantom_history.on_command(('梭哈结果', '梭哈列表'), block=True)
async def show_gacha_history(bot: Bot, ev: Event):
    """Displays today's full Echo gacha history."""
    user_id, user_name = str(ev.user_id), ev.sender.get("nickname", "Player")
    config = load_config()
    limit = config["settings"].get("daily_limit", 6)

    all_records = load_records(user_id)
    today_str = datetime.now().strftime('%Y-%m-%d')
    user_daily_results = all_records.get(today_str, {}).get(user_id)

    if not user_daily_results:
        return await bot.send(" 你今天还没有梭哈过声骸呢！", at_sender=True)

    try:
        image_objects = []
        for i, result_data in enumerate(user_daily_results):
            stats = [PhantomStat.from_dict(s) for s in result_data]
            img = await draw_single_result_card(stats, roll_number=i + 1)
            image_objects.append(img)

        tuners_remaining = limit - len(user_daily_results)

        if len(image_objects) == 1:
            final_img = await add_footer(image_objects[0], user_name, tuners_remaining)
        else:
            combined_img = await combine_images(image_objects)
            final_img = await add_footer(combined_img, user_name, tuners_remaining)

        final_img_bytes = await convert_img(final_img)
        await bot.send(final_img_bytes)
    except Exception as e:
        logger.exception(f"Failed to create history image for user {user_id}: {e}")
