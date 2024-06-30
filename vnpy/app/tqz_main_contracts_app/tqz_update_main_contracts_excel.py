import pandas

from vnpy.app.tqz_main_contracts_app.main_contracts_data_file_path import TQZMainContractsChangeFilePath
from vnpy.trader.tqz_server_data import TQZServerData

from vnpy.app.tqz_main_contracts_app.tqz_constant import (
    TQZMainContractsColumnType,
    TQZMainContractsSheetType
)

class TQZUpdateMainContractsExcel:
    """
    Load main contracts of current futures market
    """

    @classmethod
    def tqz_update_main_contracts_excel(cls):
        """
        Load main contracts from TqSdk
        """
        main_contracts = TQZServerData().tqz_load_main_contracts()

        cls.__create_main_contracts_excel(
            current_main_vt_symbols=main_contracts
        )


    # --- private part ---
    @classmethod
    def __create_main_contracts_excel(cls, current_main_vt_symbols):
        """
        Create main-contracts-excel when excel is not exist.
        """

        main_contracts_dataframe = pandas.DataFrame(
            columns=[
                TQZMainContractsColumnType.MAIN_CONTRACT.value,
                TQZMainContractsColumnType.ENTRY_PRICE_HLA.value,
                TQZMainContractsColumnType.STANDARD_LOTS_HLA.value,
                TQZMainContractsColumnType.ENTRY_PRICE_HSR.value
            ]
        )

        main_contracts_dataframe[TQZMainContractsColumnType.MAIN_CONTRACT.value] = sorted(current_main_vt_symbols)

        cls.__to_excel(
            content_dataframe=main_contracts_dataframe,
            path=TQZMainContractsChangeFilePath.main_contracts_excel(),
            sheet_name=TQZMainContractsSheetType.CURRENT_FUTURE_MAIN_CONTRACT.value
        )

    @staticmethod
    def __to_excel(content_dataframe, path, sheet_name):
        """
        Write content_dataframe to path/excel/sheet_name
        """

        excel_writer = pandas.ExcelWriter(path=path)
        content_dataframe.to_excel(
            excel_writer,
            sheet_name=sheet_name,
            index=False,
            freeze_panes=(1, 0)
        )
        excel_writer.save()


if __name__ == '__main__':
    TQZUpdateMainContractsExcel.tqz_update_main_contracts_excel()
