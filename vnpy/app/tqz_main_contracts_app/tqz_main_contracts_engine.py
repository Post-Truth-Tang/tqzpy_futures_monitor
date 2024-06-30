import time

from vnpy.trader.tqz_extern.tqz_model import TQZMonitorTimeModel
from vnpy.app.tqz_main_contracts_app.tqz_update_main_contracts_excel import TQZUpdateMainContractsExcel
from vnpy.app.tqz_main_contracts_app.tqz_replace_contracts_to_main import TQZReplaceContractsToMain

from vnpy.app.tqz_main_contracts_app.tqz_constant import (
    TQZWeekDayType
)

class TQZMainContractsEngine:

    __today_main_contracts_has_load = False
    __today_main_contracts_has_change = False
    __current_day = -1

    @classmethod
    def tqz_monitor_start(cls):

        while True:
            # init when new day
            cls.__init_today()

            if cls.__current_day in [TQZWeekDayType.SATURDAY.value, TQZWeekDayType.SUNDAY.value]:
                if time.localtime().tm_sec is 0 and time.localtime().tm_min is 0:
                    print("today is weekend, no operator to change main contracts")
                pass
            else:
                if cls.__is_refresh_time(now_time=time.localtime().tm_sec, interval_time=5):
                    print(time.strftime("%Y/%m/%d  %H:%M:%S", time.localtime()))

                    # load main contracts from tq
                    if TQZMonitorTimeModel.is_load_main_contracts_time() is True:
                        cls.tqz_update_main_contracts_excel()

                    # change main contract to per path
                    if TQZMonitorTimeModel.is_change_main_contracts_time() is True:
                        cls.tqz_replace_contracts_to_main()

            time.sleep(1)

    @classmethod
    def tqz_update_main_contracts_excel(cls):
        """
        Update main-contracts-data excel.
        """

        if cls.__today_main_contracts_has_load is False:
            cls.__today_main_contracts_has_load = True
            TQZUpdateMainContractsExcel.tqz_update_main_contracts_excel()

    @classmethod
    def tqz_replace_contracts_to_main(cls):
        """
        Replace excel data to main contracts data
        """

        if cls.__today_main_contracts_has_change is False:
            cls.__today_main_contracts_has_change = True
            TQZReplaceContractsToMain.tqz_replace_contracts_to_main()

    # --- private part ---
    @classmethod
    def __init_today(cls):
        """
        Init today data when new day is coming or restart program.
        """

        if cls.__current_day is not time.localtime().tm_wday:
            cls.__current_day = time.localtime().tm_wday
            cls.__today_main_contracts_has_load = False
            cls.__today_main_contracts_has_change = False

    @staticmethod
    def __is_refresh_time(now_time, interval_time):
        """
        Judge current time need callback or not
        """

        if now_time % interval_time is 0:
            should_refresh = True
        else:
            should_refresh = False

        return should_refresh


if __name__ == '__main__':
    TQZMainContractsEngine.tqz_monitor_start()
