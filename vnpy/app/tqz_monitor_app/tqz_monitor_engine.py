
from remi.server import Server

from vnpy.app.tqz_monitor_app.tqz_monitor_accounts_web import TQZMonitorAccountsWeb


class TQZMonitorEngine:

    def __init__(self, web_class):
        self.web_class = web_class

    def tqz_start(self, port):
        """
        Start load web according to self.web_class
        """

        Server(
            gui_class=self.web_class,
            update_interval=1,
            port=port,
            start_browser=True
        )  # 参数 update_interval: 程序每1s调用一次 idel() 函数;


if __name__ == '__main__':
    # http://127.0.0.1:8877/
    TQZMonitorEngine(web_class=TQZMonitorAccountsWeb).tqz_start(port=8877)
