from remi.server import App, Server
import remi.gui as gui
import time

from vnpy.app.tqz_monitor_app.tqz_auto_report_data_filter import TQZAutoReportDataFilter
from vnpy.app.tqz_monitor_app.tqz_auto_report import TQZAutoReport
from vnpy.app.tqz_monitor_app.tqz_future_market_sedimentary_fund import TQZFutureMarketSedimentaryFund

from vnpy.trader.tqz_extern.tools.position_operator.position_operator import TQZJsonOperator
from vnpy.trader.tqz_extern.tools.file_path_operator.file_path_operator import TQZFilePathOperator

from vnpy.trader.tqz_extern.tqz_model import (
    TQZAccountModel,
    TQZMonitorTimeModel
)

from vnpy.app.tqz_monitor_app.tqz_constant import (
    TQZDropdownSelected,
    TQZAccountKeyType,
    TQZMonitorWebDataType,
    TQZWeekDayType
)


class TQZMonitorAccountsWeb(App):

    def __init__(self, *args):

        self.__current_hour = -1
        self.__today_sedimentary_fund_has_loaded = False

        self.accounts_data_jsonfile = TQZFilePathOperator.current_file_grandfather_path(
            file=TQZFilePathOperator.grandfather_path(source_path=__file__)
        ) + f'/.vntrader/accounts_data/accounts_data.json'

        self.__yestertay_accounts_data_jsonfile = TQZFilePathOperator.current_file_father_path(
            file=__file__
        ) + f'/yesterday_accounts_data.json'

        super(TQZMonitorAccountsWeb, self).__init__(*args)


    def idle(self):

        if self.__is_refresh_time(now_time=time.localtime().tm_sec, interval_time=5) is True:

            # monitor web: 7(day) X 24(hour);
            self.__web_refresh()

            print(self.__time_now())

            # monitor yesterday_accounts_data part
            self.tqz_monitor_yesterday_accounts_data_jsonfile()

            # monitor sedimentary_fund_data_excel part
            self.tqz_monitor_sedimentary_fund_data_excel()

            # monitor auto_report part
            self.tqz_monitor_auto_report_part()


    def tqz_monitor_yesterday_accounts_data_jsonfile(self):
        """
        monitor yesterday_accounts_data jsonfile.
        monitor time: 15:30 - 15:35 (5 days)
        """

        if time.localtime().tm_wday in [TQZWeekDayType.SATURDAY.value, TQZWeekDayType.SUNDAY.value]:  # [0, 6]
            return

        if TQZMonitorTimeModel.is_record_settlement_jsonfile_time() is False:
            return

        yesterday_accounts_data = TQZJsonOperator.tqz_load_jsonfile(jsonfile=self.__yestertay_accounts_data_jsonfile)
        if yesterday_accounts_data != self.__pre_accounts_data_list:
            TQZJsonOperator.tqz_write_jsonfile(
                content=self.__pre_accounts_data_list,
                target_jsonfile=self.__yestertay_accounts_data_jsonfile
            )


    def tqz_monitor_sedimentary_fund_data_excel(self):
        """
        monitor sedimentary_fund_data excel.
        monitor time: 15:35 - 15:45 (5 days)
        """
        if time.localtime().tm_wday in [TQZWeekDayType.SATURDAY.value, TQZWeekDayType.SUNDAY.value]:  # time.localtime().tm_wday in [0, 6]
            return

        if TQZMonitorTimeModel.is_load_sedimentary_fund_time() is False:
            self.__today_sedimentary_fund_has_loaded = False
            return

        if self.__is_refresh_time(
            now_time=time.localtime().tm_sec, interval_time=60
        ) is False:  # monitor frequency of sedimentary_fund_data(60s)
            return

        if self.__today_sedimentary_fund_has_loaded is False:
            self.__today_sedimentary_fund_has_loaded = TQZFutureMarketSedimentaryFund.tqz_update_futureMarketSedimentaryFund_excel()


    def tqz_monitor_auto_report_part(self):
        """
        monitor auto report.
        monitor time: 15:45-20:15 (7 days).
        """

        if TQZMonitorTimeModel.is_auto_report_time() is False:
            return

        if self.__is_refresh_time(
            now_time=time.localtime().tm_sec, interval_time=60
        ) is False:  # monitor frequency of auto report(60s)
            return

        if self.__current_hour is not time.localtime().tm_hour:  # new hour
            print("self.__current_hour: " + str(self.__current_hour))
            self.__current_hour = time.localtime().tm_hour
            if self.__current_hour in [15, 16, 20]:
                TQZAutoReport.tqz_update(settlement_jsonfile=self.__yestertay_accounts_data_jsonfile)

                if self.__current_hour in [15]:
                    TQZAutoReportDataFilter.filter_daily_data()
                elif self.__current_hour in [16]:
                    pass  # copy data and send to weixin or blablabla...

    def main(self):
        self.__app_load_data()

        return self.__add_child_widgets()

    # private part
    # - app load data / add child widgets -
    def __app_load_data(self):
        all_account_data_list = self.__get_current_accounts_data_list(accounts_data_jsonfile=self.accounts_data_jsonfile)

        self.all_account_data_model_list = []
        [self.all_account_data_model_list.append(
            TQZAccountModel(
                account_id=account_data[TQZAccountKeyType.ACCOUNT_ID_KEY.value],
                balance=account_data[TQZAccountKeyType.BALANCE_KEY.value],
                risk_percent=account_data[TQZAccountKeyType.RISK_PERCENT_KEY.value],
                yesterday_accounts_data=TQZJsonOperator.tqz_load_jsonfile(jsonfile=self.__yestertay_accounts_data_jsonfile)
            )
        ) for account_data in all_account_data_list]

        self.now_time_second = None
        self.current_dropDown_select = TQZDropdownSelected.NUMBER.value


    def __add_child_widgets(self):
        self.layout_width = '60%'
        self.window = gui.VBox(width='100%')  # full window

        # dropDown:排序选择
        self.drop_down = self.__get_dropDown()

        # time_label控件: 当前时间
        self.time_label = self.__get_time_label()

        # table控件: 账户对应的持仓数据
        self.table = self.__get_table_list()

        return self.__window_add_subviews(
            self.drop_down,
            self.time_label,
            self.table,
            window=self.window
        )

    # -- dropDown widget part --
    def __get_dropDown(self):
        drop_down = gui.DropDown.new_from_list(
            (
                TQZDropdownSelected.NUMBER.value,
                TQZDropdownSelected.BALANCE.value,
                TQZDropdownSelected.RISKPERCENT.value,
                TQZDropdownSelected.PROFIT_AND_LOSS.value
            ),
            width=self.layout_width
        )
        drop_down.onchange.do(self.__drop_down_change)
        drop_down.select_by_value(TQZDropdownSelected.NUMBER.value)

        return drop_down

    def __drop_down_change(self, widget, selected_item):  # noqa
        self.current_dropDown_select = selected_item

        self.__web_refresh()

    # -- time label widget part --
    def __get_time_label(self):
        label_test = '更新时间: ' + self.__time_now()
        return gui.Label(label_test, width=self.layout_width, height='20%')  # 控件: label

    @staticmethod
    def __time_now():
        return time.strftime("%Y/%m/%d  %H:%M:%S", time.localtime())

    # -- table widget part --
    def __get_table_list(self):
        content_data = self.__load_table_data()
        return gui.Table.new_from_list(
            content=content_data,
            width=self.layout_width,
            fill_title=True
        )  # fill_title: True代表第一行是蓝色, False代表表格内容全部同色

    def __load_table_data(self):
        title_cell = (
            TQZMonitorWebDataType.NUMBER.value,
            TQZMonitorWebDataType.INVESTOR.value,
            TQZMonitorWebDataType.ACCOUNT_ID.value,
            TQZMonitorWebDataType.BALANCE.value,
            TQZMonitorWebDataType.USED_DEPOSIT.value,
            TQZMonitorWebDataType.PROFIT_AND_LOSS_TODAY.value,
            TQZMonitorWebDataType.RISK_PERCENT.value
        )
        table_data = [title_cell]

        accounts_data_list = self.__get_current_accounts_data_list(accounts_data_jsonfile=self.accounts_data_jsonfile)

        account_models = TQZAccountModel.list_to_models(
            account_data_list=accounts_data_list,
            yesterday_accounts_data=TQZJsonOperator.tqz_load_jsonfile(jsonfile=self.__yestertay_accounts_data_jsonfile)
        )

        if self.current_dropDown_select == TQZDropdownSelected.BALANCE.value:
            account_models = sorted(account_models, key=lambda account_model: account_model.balance, reverse=True)
        elif self.current_dropDown_select == TQZDropdownSelected.RISKPERCENT.value:
            account_models = sorted(account_models, key=lambda account_model: float(account_model.risk_percent), reverse=True)
        elif self.current_dropDown_select == TQZDropdownSelected.PROFIT_AND_LOSS.value:
            account_models = sorted(account_models, key=lambda account_model: float(account_model.profit_and_loss), reverse=True)
        elif self.current_dropDown_select == TQZDropdownSelected.NUMBER.value:
            account_models = sorted(account_models, key=lambda account_model: float(account_model.account_number), reverse=False)

        total_balance = 0
        total_available = 0
        total_used_deposit = 0
        total_profit_and_loss = 0
        for account in account_models:
            empty_cell = [
                str(account.account_number),
                str(account.account_name),
                str(account.account_id),
                str(account.balance),
                str(account.used_deposit),
                str(account.profit_and_loss),
                str(account.risk_percent) + "%",
            ]

            table_data.append(tuple(empty_cell))

            total_balance += account.balance
            total_available += account.available
            total_used_deposit += account.used_deposit
            total_profit_and_loss += account.profit_and_loss

        total_risk_percent_string = "0%"
        if total_balance is not 0:
            total_risk_percent_string = str(round(((total_balance - total_available) * 100) / total_balance, 2)) + "%"

        table_data.append(("------", "------", "------", "------", "------", "------", "------"))

        end_cell = (
            f'总计({len(account_models)}个): ',
            "  ",
            "  ",
            str(round(total_balance, 2)),
            str(round(total_used_deposit, 2)),
            str(round(total_profit_and_loss, 2)),
            total_risk_percent_string
        )
        table_data.append(end_cell)
        return table_data

    # -- web refresh part --
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

    def __web_refresh(self):

        self.window.remove_child(self.table)
        self.window.remove_child(self.time_label)
        self.time_label = self.__get_time_label()
        self.table = gui.Table.new_from_list(
            content=self.__load_table_data(),
            width=self.layout_width,
            fill_title=True
        )
        self.__window_add_subviews(
            self.time_label,
            self.table,
            window=self.window
        )

    @staticmethod
    def __window_add_subviews(*subviews, window):
        [window.append(subview) for subview in subviews]
        return window

    def __get_current_accounts_data_list(self, accounts_data_jsonfile):
        all_account_data_dictionary = TQZJsonOperator.tqz_load_jsonfile(jsonfile=accounts_data_jsonfile)

        if all_account_data_dictionary is None:
            all_account_data_dictionary = self.__pre_accounts_data_list
        else:
            self.__pre_accounts_data_list = all_account_data_dictionary

        account_data_list = []
        [account_data_list.append(account_data) for account_data in all_account_data_dictionary.values()]

        return account_data_list


if __name__ == '__main__':
    Server(
        gui_class=TQZMonitorAccountsWeb,
        update_interval=1,
        port=8878,
        start_browser=True
    )  # 参数 update_interval: 程序每1s调用一次 idel() 函数;