import json
from pathlib import Path
from typing import Dict

from PIL import Image
from gsuid_core.sv import get_plugin_available_prefix
from gsuid_core.help.draw_new_plugin_help import get_new_help
from gsuid_core.help.model import PluginHelp
from ....WutheringWavesUID.WutheringWavesUID.utils.image import get_footer
from ..version import TodayEchoVersion

ICON = Path(__file__).parent.parent.parent / "ICON.png"
HELP_DATA = Path(__file__).parent / "help.json"
ICON_PATH = Path(__file__).parent / "icon_path"
TEXT_PATH = Path(__file__).parent / "texture2d"


def get_help_data() -> Dict[str, PluginHelp]:
    # 读取文件内容
    with open(HELP_DATA, "r", encoding="utf-8") as file:
        return json.load(file)


plugin_help = get_help_data()

async def get_help(pm: int):
    try:
        PREFIX = get_plugin_available_prefix("TodayEcho")
    except ImportError:
        PREFIX = ""
    return await get_new_help(
        plugin_name="小维梭哈",
        plugin_info={f"v{TodayEchoVersion}": ""},
        plugin_icon=Image.open(ICON),
        plugin_help=plugin_help,
        plugin_prefix=PREFIX,
        help_mode="dark",
        banner_bg=Image.open(TEXT_PATH / "banner_bg.jpg"),
        banner_sub_text="梭哈模拟器",
        help_bg=Image.open(TEXT_PATH / "bg.jpg"),
        cag_bg=Image.open(TEXT_PATH / "cag_bg.png"),
        item_bg=Image.open(TEXT_PATH / "item.png"),
        icon_path=ICON_PATH,
        footer=get_footer(),
        enable_cache=True,
        column=4,
        pm=pm,
    )
