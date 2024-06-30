import os

from vnpy.trader.tqz_extern.tools.file_path_operator.file_path_operator import TQZFilePathOperator
from vnpy.trader.tqz_extern.tools.pandas_operator.pandas_operator import pandas
from vnpy.trader.tqz_server_data import TQZServerData
from vnpy.app.tqz_monitor_app.monitor_data_file_path import TQZFutureMarketSedimentaryFundFilePath

from vnpy.app.tqz_monitor_app.tqz_constant import (
    TQZSedimentaryFundSheetType,
    TQZSedimentaryFundColumnType,
    TQZCurrentFutureContractColumnType
)

class TQZFutureMarketSedimentaryFund:

    @classmethod
    def tqz_update_futureMarketSedimentaryFund_excel(cls):
        """
        Api about update excel of future market sedimentary fund
        """

        TQZFutureMarketSedimentaryFundFilePath.ensure_futureMarketSedimentaryFund_fold_is_exist()

        current_future_contracts_dataframe = TQZServerData().tqz_load_current_future_contracts_dataframe()

        if os.path.exists(TQZFutureMarketSedimentaryFundFilePath.futureMarketSedimentaryFund_excel_path()) is False:
            print("create future_market_fund.xlsx")
            cls.__create_futureMarketSedimentaryFund_excel(
                current_future_contracts_dataframe=current_future_contracts_dataframe
            )
        else:
            print("future_market_fund.xlsx is exist")
            cls.__update_futureMarketSedimentaryFund_excel_last_line(
                current_future_contracts_dataframe=current_future_contracts_dataframe
            )

        return cls.__today_is_update()

    # --- private part ---
    @classmethod
    def __today_is_update(cls):
        sedimentary_fund_dataframe = pandas.read_excel(
            io=TQZFutureMarketSedimentaryFundFilePath.futureMarketSedimentaryFund_excel_path(),
            sheet_name=TQZSedimentaryFundSheetType.FUTURE_MARKET_SEDIMENTARY_FUND.value
        )
        return TQZFutureMarketSedimentaryFundFilePath.today_string() in pandas.to_datetime(sedimentary_fund_dataframe[TQZSedimentaryFundColumnType.DATE.value].values.tolist())

    @classmethod
    def __create_futureMarketSedimentaryFund_excel(cls, current_future_contracts_dataframe):
        """
        Create future-market-sedimentary-fund excel.
        """

        market_fund_today_sum = current_future_contracts_dataframe[TQZCurrentFutureContractColumnType.SEDIMENTARY_FUND_TODAY.value].sum()

        sedimentary_fund_dataframe = pandas.DataFrame(columns=[
            TQZSedimentaryFundColumnType.DATE.value,
            TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_TODAY.value
        ])

        new_row = len(sedimentary_fund_dataframe)
        sedimentary_fund_dataframe.loc[new_row, TQZSedimentaryFundColumnType.DATE.value] = TQZServerData.today_string()
        sedimentary_fund_dataframe.loc[new_row, TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_TODAY.value] = market_fund_today_sum

        cls.__to_excel(
            dataframe=sedimentary_fund_dataframe,
            excel_path=TQZFutureMarketSedimentaryFundFilePath.futureMarketSedimentaryFund_excel_path(),
            sheet_name=TQZSedimentaryFundSheetType.FUTURE_MARKET_SEDIMENTARY_FUND.value
        )

    @classmethod
    def __update_futureMarketSedimentaryFund_excel_last_line(cls, current_future_contracts_dataframe):
        """
        Update last line of future market sedimentary fund excel.
        """

        sedimentary_fund_dataframe = pandas.read_excel(
            io=TQZFutureMarketSedimentaryFundFilePath.futureMarketSedimentaryFund_excel_path(),
            sheet_name=TQZSedimentaryFundSheetType.FUTURE_MARKET_SEDIMENTARY_FUND.value
        )

        market_sedimentary_fund_today_sum = current_future_contracts_dataframe[
            TQZCurrentFutureContractColumnType.SEDIMENTARY_FUND_TODAY.value
        ].sum()

        date_list = pandas.to_datetime(
            sedimentary_fund_dataframe[TQZSedimentaryFundColumnType.DATE.value].values.tolist()
        )
        if TQZFutureMarketSedimentaryFundFilePath.today_string() in date_list:
            sedimentary_fund_dataframe.drop(
                index=sedimentary_fund_dataframe.loc[(sedimentary_fund_dataframe[TQZSedimentaryFundColumnType.DATE.value] == TQZFutureMarketSedimentaryFundFilePath.today_string())].index,
                inplace=True
            )

        new_row = len(sedimentary_fund_dataframe)
        sedimentary_fund_dataframe.loc[
            new_row, TQZSedimentaryFundColumnType.DATE.value
        ] = TQZServerData.today_string()
        sedimentary_fund_dataframe.loc[
            new_row, TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_TODAY.value
        ] = market_sedimentary_fund_today_sum

        sedimentary_fund_dataframe[
            TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_CHANGE.value
        ] = sedimentary_fund_dataframe[
            TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_TODAY.value
        ].shift(1)

        sedimentary_fund_dataframe[
            TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_CHANGE.value
        ] = sedimentary_fund_dataframe[
            TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_TODAY.value
        ] - sedimentary_fund_dataframe[
            TQZSedimentaryFundColumnType.SEDIMENTARY_FUND_CHANGE.value
        ]

        cls.__to_excel(
            dataframe=sedimentary_fund_dataframe,
            excel_path=TQZFutureMarketSedimentaryFundFilePath.futureMarketSedimentaryFund_excel_path(),
            sheet_name=TQZSedimentaryFundSheetType.FUTURE_MARKET_SEDIMENTARY_FUND.value
        )

    @classmethod
    def __to_excel(cls, dataframe, excel_path, sheet_name, freeze_panes=(1, 0), empty_others=False):
        """
        Write dataframe to excel.
        """

        if empty_others is True:
            currrent_father_path = TQZFilePathOperator.father_path(source_path=excel_path)
            for file_name in os.listdir(currrent_father_path):
                os.remove(path=currrent_father_path + f'/{file_name}')

        excel_writer = pandas.ExcelWriter(path=excel_path)
        dataframe.to_excel(excel_writer, sheet_name=sheet_name, index=False, freeze_panes=freeze_panes)
        excel_writer.save()


if __name__ == '__main__':
    today_is_update = TQZFutureMarketSedimentaryFund.tqz_update_futureMarketSedimentaryFund_excel()
    assert today_is_update is True, f'update error'

    # # TODO 判断当天日期是否在沉淀资金数据源中
    # print("today: " + str(TQZServerData.today_string()))
