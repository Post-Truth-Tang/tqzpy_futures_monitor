import os
import re
import pandas
from datetime import datetime

from vnpy.trader.tqz_extern.tools.file_path_operator.file_path_operator import TQZFilePathOperator
from vnpy.trader.tqz_extern.tools.position_operator.position_operator import TQZJsonOperator

from vnpy.trader.tqz_extern.tools.pandas_operator.pandas_operator import TQZPandas
TQZPandas.pre_set()

from vnpy.app.tqz_monitor_app.monitor_data_file_path import (
    TQZAutoReportFilePath,
    TQZAutoReportFileCopyPath
)

from vnpy.app.tqz_monitor_app.tqz_constant import (
    TQZAutoReportSheetType,
    TQZAutoReportTotalBalanceFollowingColumnType,
    TQZAccountNameType
)

class TQZAutoReportDataFilter:
    __accounts_name_setting_path = TQZFilePathOperator.current_file_grandfather_path(
        file=TQZFilePathOperator.grandfather_path(source_path=__file__)
    ) + f'/.vntrader/accounts_name_setting.json'

    @classmethod
    def filter_daily_data(cls):

        # return when today data is not update
        if cls.__today_data_is_update(
                current_total_data_fold=cls.__current_total_data_path()
        ) is False:
            return

        # current total_data
        total_data = pandas.read_excel(
            io=cls.__current_total_data_path(),
            sheet_name=TQZAutoReportSheetType.BALANCE_TOTLE_FOLLOWING.value
        )
        total_data.set_index(TQZAutoReportTotalBalanceFollowingColumnType.DATE_ACCOUNT.value, inplace=True)

        # return when today have not data.
        if datetime.strptime(TQZAutoReportFilePath.today_string() + ' 00:00:00', '%Y-%m-%d %H:%M:%S') not in total_data.index.tolist():
            return

        TQZAutoReportFileCopyPath.init_autoReportDataCopyFold()
        cls.__copy_today_data(total_data=total_data)


    # --- private part ---
    @classmethod
    def __copy_today_data(cls, total_data):
        """
        copy today running data to auto-report-data-copy fold.
        """

        for current_account in cls.__get_current_accounts(total_data=total_data):
            source_all_path = TQZAutoReportFilePath.today_images_fold() + f'/{current_account}.png'
            target_all_path = TQZAutoReportFileCopyPath.auto_report_data_weixin_fold() + f'/{current_account}.png'
            TQZAutoReportFileCopyPath.copy_data(source_file=source_all_path, target_file=target_all_path)

        for path in os.listdir(path=TQZAutoReportFilePath.total_data_fold()):
            source_all_path = TQZAutoReportFilePath.total_data_fold() + f'/{path}'
            target_all_path = TQZAutoReportFileCopyPath.auto_report_data_weixin_fold() + f'/{path}'
            TQZAutoReportFileCopyPath.copy_data(source_file=source_all_path, target_file=target_all_path)


    @classmethod
    def __get_current_accounts(cls, total_data):
        """
        Get current accounts.
        """

        current_accounts = []
        for upper_name in cls.__get_all_upper_names():
            if upper_name == "simnow_test":
                continue

            account_balance = total_data.loc[TQZAutoReportFilePath.today_string()][upper_name]
            if pandas.isnull(account_balance) is False:
                current_accounts.append(upper_name)

        all_accounts_data = TQZJsonOperator.tqz_load_jsonfile(jsonfile=cls.__accounts_name_setting_path)

        accounts_names = []
        for account_name, account_data in all_accounts_data.items():
            if account_data[TQZAccountNameType.UPPER_NAME.value] in current_accounts:
                accounts_names.append(account_name)

        return accounts_names

    @classmethod
    def __current_total_data_path(cls):
        """
        Get current total data path.
        """

        total_data_fold = TQZAutoReportFilePath.total_data_fold()

        all_path = ''
        for path in os.listdir(total_data_fold):
            all_path = total_data_fold + f'/{path}'

        return all_path

    @classmethod
    def __get_all_upper_names(cls):
        """
        Get all upper names.
        """

        accounts_name_setting_data = TQZJsonOperator.tqz_load_jsonfile(jsonfile=cls.__accounts_name_setting_path)

        all_upper_names = []
        [all_upper_names.append(account_data[TQZAccountNameType.UPPER_NAME.value]) for account_data in accounts_name_setting_data.values()]

        return all_upper_names

    @classmethod
    def __today_data_is_update(cls, current_total_data_fold):
        """
        Judge today data of auto-report is update.
        """

        ret = re.search(TQZAutoReportFilePath.today_string(), current_total_data_fold)
        if ret:
            is_update = True
        else:
            is_update = False

        return is_update


if __name__ == '__main__':
    TQZAutoReportDataFilter.filter_daily_data()
