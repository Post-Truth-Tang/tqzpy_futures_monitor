
from vnpy.app.tqz_monitor_app.tqz_monitor_engine import TQZMonitorEngine

from vnpy.app.tqz_monitor_app.tqz_monitor_accounts_web import TQZMonitorAccountsWeb

if __name__ == '__main__':
    TQZMonitorEngine(web_class=TQZMonitorAccountsWeb).tqz_start(port=8877)
