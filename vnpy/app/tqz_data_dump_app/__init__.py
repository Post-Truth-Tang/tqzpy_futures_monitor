from pathlib import Path

from vnpy.trader.app import BaseApp
from vnpy.trader.constant import Direction
from vnpy.trader.object import TickData, BarData, TradeData, OrderData
from vnpy.trader.utility import BarGenerator, ArrayManager

from .base import APP_NAME
from .engine import DataDumpEngine
from .template import StrategyTemplate


class TQZDataDumpApp(BaseApp):
    """"""

    app_name = APP_NAME
    app_module = __module__
    app_path = Path(__file__).parent
    display_name = "数据落地"
    engine_class = DataDumpEngine
    widget_name = "tqz_data_dump_app"
    icon_name = "strategy.ico"
