# coding=utf-8
import time
import os
import re
import datetime
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdate
import matplotlib.font_manager as fm

from vnpy.app.tqz_monitor_app.tqz_constant import (
    TQZAutoReportSourceDataColumnType,
    TQZAutoReportPerAccountDataColumnType,
    TQZAutoReportTotalBalanceFollowingColumnType,
    TQZAutoReportSheetType,
    TQZSedimentaryFundSheetType,
    TQZSedimentaryFundColumnType,
    TQZAccountNameType,
    TQZWeekDayType
)

from vnpy.trader.tqz_extern.tools.position_operator.position_operator import TQZJsonOperator
from vnpy.trader.tqz_extern.tqz_model import TQZAccountModel
from vnpy.trader.tqz_extern.tools.file_path_operator.file_path_operator import TQZFilePathOperator
from vnpy.trader.tqz_extern.tools.pandas_operator.pandas_operator import pandas

from vnpy.app.tqz_monitor_app.monitor_data_file_path import (
    TQZAutoReportFilePath
)


class TQZAutoReport:

    __is_updating = False

    @classmethod
    def tqz_update(cls, settlement_jsonfile):
        """
        Create or Update today auto report.
        """

        if TQZAutoReport.__source_data_is_update(
            current_source_data_name=TQZAutoReportFilePath.current_source_data_excel_path()
        ) is False:
            print(f'auto-report today({TQZAutoReportFilePath.today_string()}) not update yet')
            cls.__tqz_update_today_auto_report(settlement_jsonfile=settlement_jsonfile)
        else:
            print(f'auto-report today({TQZAutoReportFilePath.today_string()}) is update all right')
            cls.__tqz_update_today_auto_report()


    # --- outer operation private part ---
    @classmethod
    def __current_source_data_dataframe(cls):
        """
        Get dataframe of current source data
        """

        data_frame = None
        if os.path.exists(TQZAutoReportFilePath.theory_source_data_excel_path()):
            data_frame = pandas.read_excel(TQZAutoReportFilePath.theory_source_data_excel_path(), sheet_name=TQZAutoReportSheetType.SOURCE_DATA.value)

        return data_frame

    @classmethod
    def __source_data_is_update(cls, current_source_data_name):
        """
        Judge source data of current day is update or not
        """

        target_string = TQZAutoReportFilePath.today_string()
        source_string = current_source_data_name

        ret = re.search(target_string, source_string)
        if ret:
            is_update = True
        else:
            is_update = False

        return is_update

    @classmethod
    def __tqz_update_today_auto_report(cls, settlement_jsonfile=None):
        """
        Update today auto report (Create today source data excel at first when settlement_jsonfile is not None)
        """

        if cls.__is_updating is True:
            return
        cls.__is_updating = True  # lock

        if settlement_jsonfile is not None:
            cls.__create_source_data_excel(settlement_jsonfile=settlement_jsonfile)

        cls.__update_per_account_data_excel()
        cls.__update_today_images()
        cls.__update_total_data_excel()
        if time.localtime().tm_wday is TQZWeekDayType.FRIDAY.value:
            cls.__update_weekly_pdfs(begin_weekday=TQZWeekDayType.FRIDAY.value)

        cls.__is_updating = False  # unlock

    # --- auto report api of private part ---
    @classmethod
    def __create_source_data_excel(cls, settlement_jsonfile):
        """
        Create dataframe about source data
        """
        TQZAutoReportFilePath.ensure_autoReportDataFold_is_exist()

        account_models = cls.__sourceData_to_modelList(settlement_jsonfile=settlement_jsonfile)

        accounts_name = []
        accounts_id = []
        accounts_balance = []
        accounts_risk_percent = []
        accounts_deposit = []  # 当日入金
        accounts_transfer = []  # 当日出金
        accounts_bonus = []  # 当日分红 (盈利分红 不动份额)

        for account_model in account_models:
            accounts_name.append(account_model.account_name)
            accounts_id.append(account_model.account_id)
            accounts_balance.append(account_model.balance)
            accounts_risk_percent.append(str(account_model.risk_percent) + "%")
            accounts_deposit.append(0)
            accounts_transfer.append(0)
            accounts_bonus.append(0)

        source_dataframe = pandas.DataFrame({
            TQZAutoReportSourceDataColumnType.ACCOUNT_NAME.value: accounts_name,
            TQZAutoReportSourceDataColumnType.ACCOUNT_ID.value: accounts_id,
            TQZAutoReportSourceDataColumnType.ACCOUNT_BALANCE.value: accounts_balance,
            TQZAutoReportSourceDataColumnType.ACCOUNT_RISK_PERCENT.value: accounts_risk_percent,
            TQZAutoReportSourceDataColumnType.ACCOUNT_DEPOSIT.value: accounts_deposit,
            TQZAutoReportSourceDataColumnType.ACCOUNT_TRANSFER.value: accounts_transfer,
            TQZAutoReportSourceDataColumnType.ACCOUNT_BONUS.value: accounts_bonus
        })

        cls.__to_excel(
            dataframe=source_dataframe,
            excel_path=TQZAutoReportFilePath.theory_source_data_excel_path(),
            sheet_name=TQZAutoReportSheetType.SOURCE_DATA.value,
            empty_others=True
        )

    @classmethod
    def __update_per_account_data_excel(cls):
        """
        Update excel data of per account after source data excel was update
        """
        if cls.__per_account_data_updateable() is False:
            return

        # source data excel
        source_dataframe_path = TQZAutoReportFilePath.theory_source_data_excel_path()
        source_dataframe = pandas.read_excel(
            io=source_dataframe_path,
            sheet_name=TQZAutoReportSheetType.SOURCE_DATA.value
        )

        # get current running accounts_id_list
        accounts_id_list = source_dataframe[TQZAutoReportSourceDataColumnType.ACCOUNT_ID.value].values.tolist()

        # 根据 account_id 拿 账户权益
        source_dataframe.set_index(TQZAutoReportSourceDataColumnType.ACCOUNT_ID.value, inplace=True)
        for account_id in accounts_id_list:

            per_account_filename = account_id + '.xlsx'
            per_account_all_path = TQZAutoReportFilePath.per_account_data_fold() + f'/{per_account_filename}'
            if per_account_filename not in os.listdir(TQZAutoReportFilePath.per_account_data_fold()):

                cls.__create_per_account_data_excel(
                    account_all_path=per_account_all_path,
                    account_balance=source_dataframe.loc[account_id][TQZAutoReportSourceDataColumnType.ACCOUNT_BALANCE.value],
                    account_deposit=source_dataframe.loc[account_id][TQZAutoReportSourceDataColumnType.ACCOUNT_DEPOSIT.value],
                    account_transfer=source_dataframe.loc[account_id][TQZAutoReportSourceDataColumnType.ACCOUNT_TRANSFER.value],
                    account_bonus=source_dataframe.loc[account_id][TQZAutoReportSourceDataColumnType.ACCOUNT_BONUS.value]
                )
            else:
                per_account_dataframe = pandas.read_excel(io=per_account_all_path, sheet_name=TQZAutoReportSheetType.PER_ACCOUNT_DATA.value)

                per_account_dataframe = cls.__per_account_dataframe_update_last_line(
                    per_account_dataframe=per_account_dataframe,
                    account_balance=source_dataframe.loc[account_id][TQZAutoReportSourceDataColumnType.ACCOUNT_BALANCE.value],
                    account_deposit=source_dataframe.loc[account_id][TQZAutoReportSourceDataColumnType.ACCOUNT_DEPOSIT.value],
                    account_transfer=source_dataframe.loc[account_id][TQZAutoReportSourceDataColumnType.ACCOUNT_TRANSFER.value],
                    account_bonus=source_dataframe.loc[account_id][TQZAutoReportSourceDataColumnType.ACCOUNT_BONUS.value]
                )

                cls.__to_excel(
                    dataframe=per_account_dataframe,
                    excel_path=per_account_all_path,
                    sheet_name=TQZAutoReportSheetType.PER_ACCOUNT_DATA.value,
                    empty_others=False
                )

    @classmethod
    def __update_today_images(cls):
        """
        Update today images of current running accounts.
        """

        for file_name in os.listdir(TQZAutoReportFilePath.today_images_fold()):
            os.remove(path=TQZAutoReportFilePath.today_images_fold() + f'/{file_name}')

        current_running_account_list = cls.__current_source_data_dataframe()[TQZAutoReportSourceDataColumnType.ACCOUNT_ID.value].values.tolist()

        for file_name in os.listdir(TQZAutoReportFilePath.per_account_data_fold()):
            all_path = TQZAutoReportFilePath.per_account_data_fold() + f'/{file_name}'

            per_account_dataframe = pandas.read_excel(io=all_path, sheet_name=TQZAutoReportSheetType.PER_ACCOUNT_DATA.value)

            account_id = file_name.split(".")[0]

            if account_id not in current_running_account_list:
                continue  # account_id not in current_running_account_list

            font_type_daily = 'Microsoft YaHei'

            plt.rcParams['font.sans-serif'] = [font_type_daily]  # 用来正常显示中文标签
            plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
            plt.style.use('seaborn-darkgrid')
            my_dpi = 96
            plt.figure(figsize=(8, 8), dpi=my_dpi)
            grid = plt.GridSpec(7, 6, wspace=2, hspace=2)
            ax1 = plt.subplot(grid[3:7, 0:10], frameon=True)
            plt.grid(axis='x')

            if len(per_account_dataframe) <= 8:
                plt.ylim(0.80, 1.2)
                ax1.xaxis.set_major_formatter(mdate.DateFormatter('%Y-%m-%d'))

                plt.xticks(pandas.date_range(per_account_dataframe.loc[1, TQZAutoReportPerAccountDataColumnType.DATE.value], per_account_dataframe.loc[len(per_account_dataframe)-1, TQZAutoReportPerAccountDataColumnType.DATE.value], freq='D'))

            plt.subplots_adjust(left=0.05, bottom=0.0, right=0.95, top=1, hspace=0.1, wspace=0.1)

            plt.plot(per_account_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value], per_account_dataframe[TQZAutoReportPerAccountDataColumnType.NET_VALUE.value], marker='', color="red", linewidth=2.5, alpha=0.6)
            for tick in ax1.get_xticklabels():
                tick.set_rotation(30)

            ax2 = plt.subplot(grid[0:3, 0:10], frameon=False)
            ax2.grid(False)
            plt.subplots_adjust(left=0.05, bottom=0.1, right=0.95, top=1, hspace=0.1, wspace=0.1)
            plt.gca().get_xaxis().set_visible(False)
            plt.gca().get_yaxis().set_visible(False)

            font_title = fm.FontProperties(family=font_type_daily, size=18, stretch=0, weight='black')
            font_data = fm.FontProperties(family=font_type_daily, size=25, stretch=0, )
            font_dataNote = fm.FontProperties(family=font_type_daily, size=10, stretch=0, weight='black')
            font_netValue = fm.FontProperties(family=font_type_daily, size=40, stretch=1, weight='medium')
            font_introduce = fm.FontProperties(family=font_type_daily, size=10, stretch=0, weight='black')

            plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

            balance = per_account_dataframe.loc[len(per_account_dataframe)-1, TQZAutoReportPerAccountDataColumnType.BALANCE.value]
            profit_and_loss = round(per_account_dataframe.loc[len(per_account_dataframe)-1, TQZAutoReportPerAccountDataColumnType.RESULT_PROFIT_AND_LOSS.value], 2)

            source_data_dataframe = cls.__current_source_data_dataframe().set_index(TQZAutoReportSourceDataColumnType.ACCOUNT_ID.value)
            risk_percent = source_data_dataframe.loc[account_id][TQZAutoReportSourceDataColumnType.ACCOUNT_RISK_PERCENT.value]

            max_dropDown_singleDay = round(per_account_dataframe[TQZAutoReportPerAccountDataColumnType.NET_VALUE_FLUCTUATION_SINGLE_DAY.value].min() * 100, 3)
            sharpe_ratio = round(per_account_dataframe.loc[len(per_account_dataframe)-1, TQZAutoReportPerAccountDataColumnType.SHARPE_RATIO.value], 2)
            max_dropDown_top = round(per_account_dataframe[TQZAutoReportPerAccountDataColumnType.MAX_DRAWDOWN.value].max() * (-1) * 100, 2)
            net_value = per_account_dataframe.loc[len(per_account_dataframe)-1, TQZAutoReportPerAccountDataColumnType.NET_VALUE.value]
            yield_rate_annualized = per_account_dataframe.loc[len(per_account_dataframe)-1, TQZAutoReportPerAccountDataColumnType.YIELD_RATE_ANNUALIZED.value]
            share = per_account_dataframe.loc[len(per_account_dataframe)-1, TQZAutoReportPerAccountDataColumnType.SHARE.value]

            ax2.text(0, 0.8, f'{cls.__get_account_image_title(account_id=account_id)} - CTA全天候', fontproperties=font_title, bbox={'facecolor': 'red', 'alpha': 0.1}, verticalalignment='bottom', horizontalalignment='left')
            ax2.text(0.11, 0.45, f'{format(int(balance), ",")}', fontproperties=font_data, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.11, 0.35, r'账户权益', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.11, 0.00, f'{format(int(profit_and_loss), ",")}', fontproperties=font_data, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.11, -0.10, r'累计盈利', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')

            ax2.text(0.35, 0.45, f'{risk_percent}', fontproperties=font_data, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.35, 0.35, r'风险度', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.35, 0.00, f'{max_dropDown_singleDay}%', fontproperties=font_data, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.35, -0.10, r'最大单日回撤', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')

            ax2.text(0.55, 0.45, f'{sharpe_ratio}', fontproperties=font_data, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.55, 0.35, r'夏普比率', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.57, 0.00, f'{max_dropDown_top}%', fontproperties=font_data, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.57, -0.10, r'最大高点回撤', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')

            ax2.text(0.80, 0.80, f'{round(net_value, 4)}', fontproperties=font_netValue, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.80, 0.68, r'累计净值', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')

            ax2.text(0.81, 0.55, f'{round(yield_rate_annualized * 100, 3)}%', fontproperties=font_data, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.81, 0.45, r'年化收益率', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')

            ax2.text(0.73, 0.35, r'*产品说明', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.74, 0.27, r'投资范围:', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.80, 0.27, r'股指、国债、商品期货', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='left')
            ax2.text(0.74, 0.19, r'起始日期:', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')

            start_day = per_account_dataframe.loc[0, TQZAutoReportPerAccountDataColumnType.DATE.value].to_pydatetime()
            ax2.text(0.80, 0.19, f'{start_day.year}-{start_day.month}-{start_day.day}', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='left')
            ax2.text(0.74, 0.11, r'产品份额:', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')

            ax2.text(0.80, 0.11, f'{int(share)}', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='left')

            end_day = per_account_dataframe.loc[len(per_account_dataframe) - 1, TQZAutoReportPerAccountDataColumnType.DATE.value].to_pydatetime()
            ax2.text(0.00, 0.73, f'{end_day.year}-{end_day.month}-{end_day.day}', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='left')
            ax2.text(0.12, 0.73, f'{str(account_id)}', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='left')

            plt.savefig(f"{TQZAutoReportFilePath.today_images_fold()}/{account_id}.png")
            plt.close("all")

    @classmethod
    def __update_total_data_excel(cls):
        """
        Update total data excel
        """

        # source data of all accounts
        account_id_account_dataframe_dictionary = cls.__init_account_id_account_dataframe_dictionary()

        # create new total_balance_following dataframe | balance_fluctuation_singleDay_dataframe | profit_and_loss_total_dataframe
        total_balance_following_dataframe = cls.__init_total_balance_following_dataframe(account_id_account_dataframe_dictionary=account_id_account_dataframe_dictionary)
        balance_fluctuation_singleDay_dataframe = cls.__init_balance_fluctuation_singleDay_dataframe(account_id_account_dataframe_dictionary=account_id_account_dataframe_dictionary)
        profit_and_loss_total_dataframe = cls.__init_profit_and_loss_total_dataframe(account_id_account_dataframe_dictionary=account_id_account_dataframe_dictionary)

        # all accounts by sort in date
        ACCOUNT_ABBR = "账户缩写"
        date_sort_dataframe = pandas.DataFrame(columns=[TQZAutoReportPerAccountDataColumnType.DATE.value, TQZAutoReportSourceDataColumnType.ACCOUNT_ID.value, ACCOUNT_ABBR])
        for account_id, per_account_dataframe in account_id_account_dataframe_dictionary.items():
            new_column = len(date_sort_dataframe)
            date_sort_dataframe.loc[new_column, TQZAutoReportPerAccountDataColumnType.DATE.value] = per_account_dataframe.iloc[0][TQZAutoReportPerAccountDataColumnType.DATE.value]
            date_sort_dataframe.loc[new_column, TQZAutoReportSourceDataColumnType.ACCOUNT_ID.value] = account_id
            date_sort_dataframe.loc[new_column, ACCOUNT_ABBR] = cls.__get_account_image_title(account_id=account_id)

        date_sort_dataframe.sort_values(TQZAutoReportPerAccountDataColumnType.DATE.value, inplace=True)
        account_id_list = date_sort_dataframe[TQZAutoReportSourceDataColumnType.ACCOUNT_ID.value].values.tolist()
        account_name_list = date_sort_dataframe[ACCOUNT_ABBR].values.tolist()

        # add new account_name columns to total_balance_following_dataframe
        for account_id in account_id_list:
            per_account_dataframe = account_id_account_dataframe_dictionary[account_id]
            per_account_dataframe.set_index(
                TQZAutoReportPerAccountDataColumnType.DATE.value,
                inplace=True
            )

            balance_fluctuation_singleDay_dataframe = pandas.merge(
                left=balance_fluctuation_singleDay_dataframe,
                right=per_account_dataframe[TQZAutoReportPerAccountDataColumnType.BALANCE_FLUCTUATION_SINGLE_DAY.value],
                left_index=True,
                right_index=True,
                how='left'
            )

            profit_and_loss_total_dataframe = pandas.merge(
                left=profit_and_loss_total_dataframe,
                right=per_account_dataframe[TQZAutoReportPerAccountDataColumnType.RESULT_PROFIT_AND_LOSS.value],
                left_index=True,
                right_index=True,
                how='left'
            )

            total_balance_following_dataframe.loc[:, cls.__get_account_image_title(
                account_id=account_id
            )] = per_account_dataframe[TQZAutoReportPerAccountDataColumnType.BALANCE.value]

        # add TOTAL_BALANCE | PRIFIT_AND_LOSS_TODAY | PROFIT_AND_LOSS_TODAY_PERCENT | PROFIT_AND_LOSS_TOTAL | PROFIT_AND_LOSS_TOTAL_HISTORY to total_balance_following_dataframe
        total_balance_following_dataframe[TQZAutoReportTotalBalanceFollowingColumnType.TOTAL_BALANCE.value] = round(total_balance_following_dataframe[account_name_list].sum(axis=1), 0)

        total_balance_following_dataframe[TQZAutoReportTotalBalanceFollowingColumnType.PROFIT_AND_LOSS_TODAY.value] = round(balance_fluctuation_singleDay_dataframe[:].sum(axis=1), 0)

        total_balance_following_dataframe[TQZAutoReportTotalBalanceFollowingColumnType.PROFIT_AND_LOSS_TODAY_PERCENT.value] = round((total_balance_following_dataframe[TQZAutoReportTotalBalanceFollowingColumnType.PROFIT_AND_LOSS_TODAY.value] / total_balance_following_dataframe[TQZAutoReportTotalBalanceFollowingColumnType.TOTAL_BALANCE.value]) * 100, 3)
        total_balance_following_dataframe[TQZAutoReportTotalBalanceFollowingColumnType.PROFIT_AND_LOSS_TODAY_PERCENT.value] = total_balance_following_dataframe[TQZAutoReportTotalBalanceFollowingColumnType.PROFIT_AND_LOSS_TODAY_PERCENT.value].astype(str) + "%"

        total_balance_following_dataframe[TQZAutoReportTotalBalanceFollowingColumnType.PROFIT_AND_LOSS_TOTAL.value] = round(profit_and_loss_total_dataframe[:].sum(axis=1), 0)

        profit_and_loss_total_dataframe.fillna(method="ffill", inplace=True)  # 缺失值的数据由上一行的数据来补齐
        total_balance_following_dataframe[TQZAutoReportTotalBalanceFollowingColumnType.PROFIT_AND_LOSS_TOTAL_HISTORY.value] = round(profit_and_loss_total_dataframe[:].sum(axis=1), 0)

        total_balance_following_dataframe = cls.__add_sedimentary_fund_data(
            total_balance_following_dataframe=total_balance_following_dataframe
        )

        # delete hour|minute|second when write to excel
        total_balance_following_dataframe[
            TQZAutoReportTotalBalanceFollowingColumnType.DATE_ACCOUNT.value
        ] = total_balance_following_dataframe[
            TQZAutoReportTotalBalanceFollowingColumnType.DATE_ACCOUNT.value
        ].dt.date

        cls.__to_excel(
            dataframe=total_balance_following_dataframe,
            excel_path=TQZAutoReportFilePath.total_data_fold() + f'/total_data({TQZAutoReportFilePath.today_string()}).xlsx',
            sheet_name=TQZAutoReportSheetType.BALANCE_TOTLE_FOLLOWING.value,
            freeze_panes=(1, 1),
            empty_others=True
        )

    @classmethod
    def __update_weekly_pdfs(cls, begin_weekday):
        """
        Update weekly pdfs of current running accounts.
        """

        for file_name in os.listdir(TQZAutoReportFilePath.weekly_pdfs_fold()):
            os.remove(path=TQZAutoReportFilePath.weekly_pdfs_fold() + f'/{file_name}')

        current_running_account_list = cls.__current_source_data_dataframe()[
            TQZAutoReportSourceDataColumnType.ACCOUNT_ID.value
        ].values.tolist()

        for file_name in os.listdir(TQZAutoReportFilePath.per_account_data_fold()):
            all_path = TQZAutoReportFilePath.per_account_data_fold() + f'/{file_name}'

            per_account_dataframe = pandas.read_excel(
                io=all_path,
                sheet_name=TQZAutoReportSheetType.PER_ACCOUNT_DATA.value
            )

            per_account_dataframe = per_account_dataframe.loc[per_account_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value].dt.dayofweek == begin_weekday, :]
            per_account_dataframe.reset_index(inplace=True)

            if len(per_account_dataframe) < 2:
                continue

            account_id = file_name.split(".")[0]

            if account_id not in current_running_account_list:
                continue  # account_id not in current_running_account_list

            font_type_pdf_weekly = 'KaiTi'

            plt.rcParams['font.sans-serif'] = [font_type_pdf_weekly]  # 用来正常显示中文标签
            plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
            plt.style.use('seaborn-darkgrid')
            my_dpi = 96
            plt.figure(figsize=(8, 8), dpi=my_dpi)
            grid = plt.GridSpec(7, 6, wspace=2, hspace=2)
            ax1 = plt.subplot(grid[3:7, 0:10], frameon=True)
            plt.grid(axis='x')

            if len(per_account_dataframe) <= 8:
                plt.ylim(0.80, 1.2)
                ax1.xaxis.set_major_formatter(mdate.DateFormatter('%Y-%m-%d'))

                plt.xticks(pandas.date_range(per_account_dataframe.loc[0, TQZAutoReportPerAccountDataColumnType.DATE.value], per_account_dataframe.loc[len(per_account_dataframe) - 1, TQZAutoReportPerAccountDataColumnType.DATE.value], freq='W-FRI'))
                continue

            plt.subplots_adjust(left=0.05, bottom=0.0, right=0.95, top=1, hspace=0.1, wspace=0.1)

            plt.plot(
                per_account_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value],
                per_account_dataframe[TQZAutoReportPerAccountDataColumnType.NET_VALUE.value],
                marker='',
                color="red",
                linewidth=2.5,
                alpha=0.6
            )

            for tick in ax1.get_xticklabels():
                tick.set_rotation(30)

            ax2 = plt.subplot(grid[0:3, 0:10], frameon=False)
            ax2.grid(False)
            plt.subplots_adjust(left=0.05, bottom=0.1, right=0.95, top=1, hspace=0.1, wspace=0.1)
            plt.gca().get_xaxis().set_visible(False)
            plt.gca().get_yaxis().set_visible(False)

            font_title = fm.FontProperties(family=font_type_pdf_weekly, size=18, stretch=0, weight='black')
            font_data = fm.FontProperties(family=font_type_pdf_weekly, size=25, stretch=0)
            font_dataNote = fm.FontProperties(family=font_type_pdf_weekly, size=10, stretch=0, weight='black')
            font_netValue = fm.FontProperties(family=font_type_pdf_weekly, size=40, stretch=1, weight='medium')
            font_introduce = fm.FontProperties(family=font_type_pdf_weekly, size=10, stretch=0, weight='black')

            plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

            max_dropDown_singleDay = round(
                per_account_dataframe[TQZAutoReportPerAccountDataColumnType.NET_VALUE_FLUCTUATION_SINGLE_DAY.value].min() * 100,
                3
            )
            sharpe_ratio = round(
                per_account_dataframe.loc[len(per_account_dataframe) - 1, TQZAutoReportPerAccountDataColumnType.SHARPE_RATIO.value],
                2
            )
            max_dropDown_top = round(
                per_account_dataframe[TQZAutoReportPerAccountDataColumnType.MAX_DRAWDOWN.value].max() * (-1) * 100,
                2
            )
            net_value = per_account_dataframe.loc[
                len(per_account_dataframe) - 1, TQZAutoReportPerAccountDataColumnType.NET_VALUE.value
            ]
            yield_rate_annualized = round(per_account_dataframe.loc[
                len(per_account_dataframe) - 1,
                TQZAutoReportPerAccountDataColumnType.YIELD_RATE_ANNUALIZED.value
            ] * 100, 3)
            share = per_account_dataframe.loc[
                len(per_account_dataframe) - 1,
                TQZAutoReportPerAccountDataColumnType.SHARE.value
            ]

            ax2.text(0, 0.8, f'翡熙CTA组合净值报告(周度)',
                     fontproperties=font_title, bbox={'facecolor': 'red', 'alpha': 0.1}, verticalalignment='bottom',
                     horizontalalignment='left')
            ax2.text(0.11, 0.45, f'{round(per_account_dataframe[TQZAutoReportPerAccountDataColumnType.NET_VALUE.value].max(), 4)}', fontproperties=font_data,
                     bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center',
                     horizontalalignment='center')

            ax2.text(0.11, 0.35, r'净值峰值 (周度)', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0},
                     verticalalignment='center', horizontalalignment='center')
            ax2.text(0.11, 0.00, f'{max_dropDown_top}%', fontproperties=font_data, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.11, -0.10, r'最大高点回撤', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')

            ax2.text(0.35, 0.45, f'8%-15%', fontproperties=font_data, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='center')
            ax2.text(0.35, 0.35, r'保证金利用率', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0},
                     verticalalignment='center', horizontalalignment='center')
            ax2.text(0.35, 0.00, f'{max_dropDown_singleDay}%', fontproperties=font_data,
                     bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center',
                     horizontalalignment='center')
            ax2.text(0.35, -0.10, r'最大单周回撤', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0},
                     verticalalignment='center', horizontalalignment='center')

            ax2.text(0.55, 0.45, f'{sharpe_ratio}', fontproperties=font_data,
                     bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center',
                     horizontalalignment='center')
            ax2.text(0.55, 0.35, r'夏普比率', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0},
                     verticalalignment='center', horizontalalignment='center')
            ax2.text(0.57, 0.00, f'{round(yield_rate_annualized/abs(max_dropDown_top), 2)}', fontproperties=font_data,
                     bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center',
                     horizontalalignment='center')
            ax2.text(0.57, -0.10, r'收益风险比', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0},
                     verticalalignment='center', horizontalalignment='center')

            ax2.text(0.80, 0.80, f'{round(net_value, 4)}', fontproperties=font_netValue,
                     bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center',
                     horizontalalignment='center')
            ax2.text(0.81, 0.68, r'当前净值 (周度)', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0},
                     verticalalignment='center', horizontalalignment='center')

            ax2.text(0.81, 0.55, f'{yield_rate_annualized}%', fontproperties=font_data,
                     bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center',
                     horizontalalignment='center')
            ax2.text(0.81, 0.45, r'年化收益率', fontproperties=font_dataNote, bbox={'facecolor': 'yellow', 'alpha': 0.0},
                     verticalalignment='center', horizontalalignment='center')

            ax2.text(0.73, 0.35, r'*产品说明', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0},
                     verticalalignment='center', horizontalalignment='center')
            ax2.text(0.74, 0.27, r'投资范围:', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0},
                     verticalalignment='center', horizontalalignment='center')
            ax2.text(0.80, 0.27, r'股指、国债、商品期货', fontproperties=font_introduce,
                     bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='left')
            ax2.text(0.74, 0.19, r'起始日期:', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0},
                     verticalalignment='center', horizontalalignment='center')

            start_day = per_account_dataframe.loc[0, TQZAutoReportPerAccountDataColumnType.DATE.value].to_pydatetime()
            ax2.text(0.80, 0.19, f'{start_day.year}-{start_day.month}-{start_day.day}', fontproperties=font_introduce,
                     bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='left')
            ax2.text(0.74, 0.11, r'产品份额:', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0},
                     verticalalignment='center', horizontalalignment='center')

            ax2.text(0.80, 0.11, f'{int(share)}', fontproperties=font_introduce,
                     bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='left')

            end_day = per_account_dataframe.loc[
                len(per_account_dataframe) - 1, TQZAutoReportPerAccountDataColumnType.DATE.value
            ].to_pydatetime()
            ax2.text(0.00, 0.73, f'{end_day.year}-{end_day.month}-{end_day.day}', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='left')
            ax2.text(0.12, 0.73, f'{str(account_id)}', fontproperties=font_introduce, bbox={'facecolor': 'yellow', 'alpha': 0.0}, verticalalignment='center', horizontalalignment='left')

            plt.savefig(f'{TQZAutoReportFilePath.weekly_pdfs_fold()}/翡熙CTA周净值报告_{TQZAutoReportFilePath.today_string()}({cls.__get_account_image_title(account_id=account_id)}).pdf')
            plt.close("all")



    # --- inter operation private part ---
    @classmethod
    def __init_base_date_dataframe(cls, account_id_account_dataframe_dictionary):
        # concat all date dataframe of accounts
        date_dataframe = pandas.concat(
            account_id_account_dataframe_dictionary.values(),
            ignore_index=True
        )

        #  delete repeat data in DATE column
        date_dataframe = cls.__delete_repeat_date(
            source_dataframe=date_dataframe
        )

        concat_total_date_dataframe = pandas.DataFrame()
        concat_total_date_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value] = date_dataframe[
            TQZAutoReportPerAccountDataColumnType.DATE.value]

        return concat_total_date_dataframe

    @classmethod
    def __init_profit_and_loss_total_dataframe(cls, account_id_account_dataframe_dictionary):
        date_dataframe = cls.__init_base_date_dataframe(account_id_account_dataframe_dictionary=account_id_account_dataframe_dictionary)

        profit_and_loss_total_dataframe = pandas.DataFrame()
        profit_and_loss_total_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value] = date_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value]
        profit_and_loss_total_dataframe.set_index(TQZAutoReportPerAccountDataColumnType.DATE.value, inplace=True)

        return profit_and_loss_total_dataframe

    @classmethod
    def __init_balance_fluctuation_singleDay_dataframe(cls, account_id_account_dataframe_dictionary):
        date_dataframe = cls.__init_base_date_dataframe(account_id_account_dataframe_dictionary=account_id_account_dataframe_dictionary)

        balance_fluctuation_singleDay_dataframe = pandas.DataFrame()
        balance_fluctuation_singleDay_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value] = date_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value]
        balance_fluctuation_singleDay_dataframe.set_index(TQZAutoReportPerAccountDataColumnType.DATE.value, inplace=True)

        return balance_fluctuation_singleDay_dataframe

    @classmethod
    def __init_total_balance_following_dataframe(cls, account_id_account_dataframe_dictionary):

        date_dataframe = cls.__init_base_date_dataframe(account_id_account_dataframe_dictionary=account_id_account_dataframe_dictionary)

        total_balance_following_dataframe = pandas.DataFrame()
        total_balance_following_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value] = date_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value]
        total_balance_following_dataframe[TQZAutoReportTotalBalanceFollowingColumnType.DATE_ACCOUNT.value] = date_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value]
        total_balance_following_dataframe.set_index(TQZAutoReportPerAccountDataColumnType.DATE.value, inplace=True)

        return total_balance_following_dataframe

    @classmethod
    def __init_account_id_account_dataframe_dictionary(cls):

        account_id_account_dataframe_dictionary = {}

        for path in os.listdir(TQZAutoReportFilePath.per_account_data_fold()):
            account_id = path.split(".")[0]

            if account_id == "175896":
                continue

            account_id_account_dataframe_dictionary[account_id] = pandas.read_excel(
                io=TQZAutoReportFilePath.per_account_data_fold() + f'/{path}',
                sheet_name=TQZAutoReportSheetType.PER_ACCOUNT_DATA.value
            )

        [per_account_dataframe.drop(per_account_dataframe.index[0], inplace=True) for account_id, per_account_dataframe in account_id_account_dataframe_dictionary.items()]

        return account_id_account_dataframe_dictionary

    @classmethod
    def __delete_repeat_date(cls, source_dataframe):
        """
        Delete repeat data in assign column
        """

        source_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value] = pandas.to_datetime(
            source_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value]
        )

        source_dataframe.index = source_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value]
        del source_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value]
        source_dataframe = source_dataframe.groupby(TQZAutoReportPerAccountDataColumnType.DATE.value).count()
        source_dataframe.sort_index()
        source_dataframe.reset_index(inplace=True)

        return source_dataframe

    @classmethod
    def __sourceData_to_modelList(cls, settlement_jsonfile=None):
        """
        Change source_data to model_list (default order type: account balance)
        """

        account_models = TQZAccountModel.list_to_models(
            account_data_list=TQZJsonOperator.tqz_load_jsonfile(jsonfile=settlement_jsonfile).values(),
            yesterday_accounts_data={}
        )

        account_models_sortedByBalance = sorted(
            account_models,
            key=lambda tqz_account_model: tqz_account_model.balance,
            reverse=True
        )

        return account_models_sortedByBalance

    @classmethod
    def __create_per_account_data_excel(cls, account_all_path, account_balance, account_deposit=0, account_transfer=0, account_bonus=0):
        """
        Create new single account excel
        """

        columns = [
            TQZAutoReportPerAccountDataColumnType.DATE.value,
            TQZAutoReportPerAccountDataColumnType.BALANCE.value,
            TQZAutoReportPerAccountDataColumnType.SHARE.value,
            TQZAutoReportPerAccountDataColumnType.RESULT_PROFIT_AND_LOSS.value,
            TQZAutoReportPerAccountDataColumnType.NET_VALUE.value,
            TQZAutoReportPerAccountDataColumnType.MAX_DRAWDOWN.value,
            TQZAutoReportPerAccountDataColumnType.BALANCE_FLUCTUATION_SINGLE_DAY.value,
            TQZAutoReportPerAccountDataColumnType.NET_VALUE_FLUCTUATION_SINGLE_DAY.value,
            TQZAutoReportPerAccountDataColumnType.AVERAGE_VOLATILITY_SINGLE_DAY.value,
            TQZAutoReportPerAccountDataColumnType.YIELD_RATE_ANNUALIZED.value,
            TQZAutoReportPerAccountDataColumnType.YIELD_RATE_FLUCTUATION_STANDARD_DEVIATION.value,
            TQZAutoReportPerAccountDataColumnType.SHARPE_RATIO.value,
            TQZAutoReportPerAccountDataColumnType.CURRENT_DAY_DEPOSIT.value,
            TQZAutoReportPerAccountDataColumnType.CURRENT_DAY_TRANSFER.value,
            TQZAutoReportPerAccountDataColumnType.CURRENT_DAY_BONUS.value,
        ]

        per_account_dataframe = pandas.DataFrame(columns=columns)

        # default column(first column)
        first_column = len(per_account_dataframe)
        per_account_dataframe.loc[first_column, TQZAutoReportPerAccountDataColumnType.DATE.value] = datetime.date.today() - datetime.timedelta(days=1)
        per_account_dataframe.loc[first_column, TQZAutoReportPerAccountDataColumnType.CURRENT_DAY_DEPOSIT.value] = 1000 * 1e4
        per_account_dataframe.loc[first_column, TQZAutoReportPerAccountDataColumnType.BALANCE.value] = per_account_dataframe.loc[first_column, TQZAutoReportPerAccountDataColumnType.CURRENT_DAY_DEPOSIT.value]
        per_account_dataframe.loc[first_column, TQZAutoReportPerAccountDataColumnType.SHARE.value] = per_account_dataframe.loc[first_column, TQZAutoReportPerAccountDataColumnType.CURRENT_DAY_DEPOSIT.value]
        per_account_dataframe.loc[first_column, TQZAutoReportPerAccountDataColumnType.NET_VALUE.value] = 1
        per_account_dataframe.loc[first_column, TQZAutoReportPerAccountDataColumnType.YIELD_RATE_ANNUALIZED.value] = 1

        per_account_dataframe = cls.__per_account_dataframe_update_last_line(
            per_account_dataframe=per_account_dataframe,
            account_balance=account_balance,
            account_deposit=account_deposit,
            account_transfer=account_transfer,
            account_bonus=account_bonus
        )

        cls.__to_excel(
            dataframe=per_account_dataframe,
            excel_path=account_all_path,
            sheet_name=TQZAutoReportSheetType.PER_ACCOUNT_DATA.value,
            empty_others=False
        )

    @classmethod
    def __per_account_data_updateable(cls):
        """
        Can update per account data or not
        """

        can_update = True
        for path in os.listdir(TQZAutoReportFilePath.source_data_fold()):
            if cls.__source_data_is_update(
                    current_source_data_name=TQZAutoReportFilePath.source_data_fold() + f'/{path}'
            ) is False:
                can_update = False

        if len(os.listdir(TQZAutoReportFilePath.source_data_fold())) is not 1:
            can_update = False

        return can_update

    @classmethod
    def __per_account_dataframe_update_last_line(cls, per_account_dataframe, account_balance, account_deposit, account_transfer, account_bonus):
        """
        Update last line of per account dataframe
        """

        # delete data of current day when today data is exist
        date_list = per_account_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value].values.tolist()
        if TQZAutoReportFilePath.today_string() in date_list:
            per_account_dataframe = per_account_dataframe.drop(index=per_account_dataframe.loc[(per_account_dataframe[TQZAutoReportPerAccountDataColumnType.DATE.value] == TQZAutoReportFilePath.today_string())].index)

        new_row = len(per_account_dataframe)
        # do nothing when balance of previous column is equal to account_balance
        if per_account_dataframe.loc[new_row-1, TQZAutoReportPerAccountDataColumnType.BALANCE.value] == account_balance:
            if (0 == account_deposit) and (0 == account_transfer) and (0 == account_bonus):
                return per_account_dataframe
            else:
                new_row -= 1  # re write last line.

        per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.DATE.value] = TQZAutoReportFilePath.today_string()
        per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.BALANCE.value] = account_balance
        if account_deposit != 0:
            per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.CURRENT_DAY_DEPOSIT.value] = account_deposit
        if account_transfer != 0:
            per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.CURRENT_DAY_TRANSFER.value] = account_transfer
        if account_bonus != 0:
            per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.CURRENT_DAY_BONUS.value] = account_bonus

        # 份额
        old_share = per_account_dataframe.loc[new_row-1, TQZAutoReportPerAccountDataColumnType.SHARE.value]
        money_change = account_deposit + (account_transfer * -1)
        per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.SHARE.value] = old_share + (money_change / per_account_dataframe.loc[new_row - 1, TQZAutoReportPerAccountDataColumnType.NET_VALUE.value])

        # 结算盈亏
        per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.RESULT_PROFIT_AND_LOSS.value] = account_balance - per_account_dataframe[TQZAutoReportPerAccountDataColumnType.CURRENT_DAY_DEPOSIT.value].sum() + per_account_dataframe[TQZAutoReportPerAccountDataColumnType.CURRENT_DAY_BONUS.value].sum() + per_account_dataframe[TQZAutoReportPerAccountDataColumnType.CURRENT_DAY_TRANSFER.value].sum()

        # 净值
        per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.NET_VALUE.value] = round((account_balance + per_account_dataframe[TQZAutoReportPerAccountDataColumnType.CURRENT_DAY_BONUS.value].sum()) / per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.SHARE.value], 5)

        # 最大回撤
        per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.MAX_DRAWDOWN.value] = round(max(per_account_dataframe[TQZAutoReportPerAccountDataColumnType.NET_VALUE.value].max() - per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.NET_VALUE.value], 0), 5)

        # 单日权益波动
        per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.BALANCE_FLUCTUATION_SINGLE_DAY.value] = round(per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.BALANCE.value] - per_account_dataframe.loc[new_row - 1, TQZAutoReportPerAccountDataColumnType.BALANCE.value], 2) - money_change + account_bonus

        # 单日净值波动
        per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.NET_VALUE_FLUCTUATION_SINGLE_DAY.value] = round(per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.NET_VALUE.value] - per_account_dataframe.loc[new_row - 1, TQZAutoReportPerAccountDataColumnType.NET_VALUE.value], 5)

        # 年化收益率
        per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.YIELD_RATE_ANNUALIZED.value] = round(((per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.NET_VALUE.value] - 1) / len(per_account_dataframe)) * 250, 5)

        # 单日平均波动率
        per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.AVERAGE_VOLATILITY_SINGLE_DAY.value] = round(per_account_dataframe[TQZAutoReportPerAccountDataColumnType.NET_VALUE_FLUCTUATION_SINGLE_DAY.value].sum() / len(per_account_dataframe), 5)

        # 收益率波动标准差
        per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.YIELD_RATE_FLUCTUATION_STANDARD_DEVIATION.value] = per_account_dataframe[TQZAutoReportPerAccountDataColumnType.AVERAGE_VOLATILITY_SINGLE_DAY.value].std(ddof=0)

        # 夏普比率
        if 0 == per_account_dataframe[TQZAutoReportPerAccountDataColumnType.NET_VALUE_FLUCTUATION_SINGLE_DAY.value].std(ddof=0):
            per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.SHARPE_RATIO.value] = 0
        else:
            per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.SHARPE_RATIO.value] = per_account_dataframe.loc[new_row, TQZAutoReportPerAccountDataColumnType.YIELD_RATE_ANNUALIZED.value] / per_account_dataframe[TQZAutoReportPerAccountDataColumnType.NET_VALUE_FLUCTUATION_SINGLE_DAY.value].std(ddof=0) / math.sqrt(250)

        return per_account_dataframe

    @classmethod
    def __to_excel(cls, dataframe, excel_path, sheet_name, freeze_panes=(1, 0), empty_others=False):
        """
        Write dataframe to excel.
        """

        if empty_others is True:
            current_father_path = TQZFilePathOperator.father_path(source_path=excel_path)
            for file_name in os.listdir(current_father_path):
                os.remove(path=current_father_path + f'/{file_name}')

        excel_writer = pandas.ExcelWriter(path=excel_path)
        dataframe.to_excel(excel_writer, sheet_name=sheet_name, index=False, freeze_panes=freeze_panes)
        excel_writer.save()

    @classmethod
    def __get_sedimentary_fund_dataframe(cls):
        """
        Get sedimentary fund dataframe
        """

        futureMarket_SedimentaryFund_data_fold = TQZFilePathOperator.current_file_father_path(
            file=__file__
        ) + '/futureMarket_SedimentaryFund_data'
        all_path = futureMarket_SedimentaryFund_data_fold + f'/{os.listdir(futureMarket_SedimentaryFund_data_fold)[0]}'

        sedimentary_fund_dataframe = pandas.read_excel(
            io=all_path,
            sheet_name=TQZSedimentaryFundSheetType.FUTURE_MARKET_SEDIMENTARY_FUND.value
        )

        sedimentary_fund_dataframe[
            TQZAutoReportTotalBalanceFollowingColumnType.DATE_ACCOUNT.value
        ] = sedimentary_fund_dataframe[
            TQZSedimentaryFundColumnType.DATE.value
        ]
        sedimentary_fund_dataframe.set_index(
            TQZAutoReportTotalBalanceFollowingColumnType.DATE_ACCOUNT.value,
            inplace=True
        )

        return sedimentary_fund_dataframe

    @classmethod
    def __add_sedimentary_fund_data(cls, total_balance_following_dataframe):
        """
        total_balance_following_dataframe add row data about sedimentary_fund.
        """

        sedimentary_fund_dataframe = cls.__get_sedimentary_fund_dataframe()

        total_balance_following_dataframe.set_index(
            TQZAutoReportTotalBalanceFollowingColumnType.DATE_ACCOUNT.value,
            inplace=True
        )

        total_balance_following_dataframe = pandas.merge(
            left=total_balance_following_dataframe,
            right=sedimentary_fund_dataframe[TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_TODAY.value],
            left_index=True,
            right_index=True,
            how='left'
        )

        total_balance_following_dataframe = pandas.merge(
            left=total_balance_following_dataframe,
            right=sedimentary_fund_dataframe[TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_CHANGE.value],
            left_index=True,
            right_index=True,
            how='left'
        )

        total_balance_following_dataframe.reset_index(inplace=True)

        total_balance_following_dataframe[TQZAutoReportTotalBalanceFollowingColumnType.SEDIMENTARY_FUND_TODAY.value] = round(total_balance_following_dataframe[TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_TODAY.value] / 100000000, 3)
        total_balance_following_dataframe[TQZAutoReportTotalBalanceFollowingColumnType.SEDIMENTARY_FUND_CHANGE.value] = round(total_balance_following_dataframe[TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_CHANGE.value] / 100000000, 3)

        del total_balance_following_dataframe[TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_TODAY.value], total_balance_following_dataframe[TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_CHANGE.value]

        return total_balance_following_dataframe

    @classmethod
    def __get_account_image_title(cls, account_id):
        """
        Get image title of account with account id
        """

        accounts_name_setting_path = TQZFilePathOperator.current_file_grandfather_path(
            file=TQZFilePathOperator.grandfather_path(source_path=__file__)
        ) + '/.vntrader/accounts_name_setting.json'
        accounts_name_setting_content = TQZJsonOperator.tqz_load_jsonfile(jsonfile=accounts_name_setting_path)

        if account_id in accounts_name_setting_content.keys():
            return accounts_name_setting_content[account_id][TQZAccountNameType.UPPER_NAME.value]
        else:
            return "翡熙量化"


if __name__ == '__main__':
    yesterday_accounts_data_jsonfile = "yesterday_accounts_data.json"

    TQZAutoReport.tqz_update(settlement_jsonfile=yesterday_accounts_data_jsonfile)
