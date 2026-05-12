from PIL import Image

from gsuid_core.bot import Bot
from gsuid_core.help.utils import register_help
from gsuid_core.models import Event
from gsuid_core.sv import SV, get_plugin_available_prefix

from .get_help import ICON, get_help

sv_rover_help = SV("TodayEcho帮助")


@sv_rover_help.on_fullmatch(
    "梭哈帮助",
    to_ai="""返回 TodayEcho（鸣潮声骸梭哈模拟器）插件的命令帮助图。

当用户问「梭哈帮助 / 模拟梭哈怎么用 / today echo help」时调用。

Args:
    text: 无需参数。
""",
)
async def send_help_img(bot: Bot, ev: Event):
    await bot.send(await get_help(ev.user_pm))


PREFIX = get_plugin_available_prefix("TodayEcho")
register_help("WWUID-TE", f"{PREFIX}梭哈帮助", Image.open(ICON))