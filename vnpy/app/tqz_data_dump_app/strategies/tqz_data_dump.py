from vnpy.app.tqz_data_dump_app import StrategyTemplate


class TQZDataDump(StrategyTemplate):

    author = "Post-Truth"

    def __init__(self, strategy_engine, strategy_name, vt_symbols, setting):
        """  """
        super().__init__(strategy_engine, strategy_name, vt_symbols, setting)

        print("TQZDataDump init")

        self.vt_symbols = []


    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")

        print("TQZDataDump on_init")


    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

        print("TQZDataDump on_start")


    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

        print("TQZDataDump on_stop")
