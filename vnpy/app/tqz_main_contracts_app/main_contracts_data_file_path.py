
import os

from vnpy.trader.tqz_extern.tools.file_path_operator.file_path_operator import TQZFilePathOperator

class TQZMainContractsChangeFilePath:

    @classmethod
    def main_contract_data_fold(cls):
        return TQZFilePathOperator.current_file_father_path(file=__file__) + '/main_contract_data'

    @classmethod
    def main_contracts_excel(cls):
        return cls.main_contract_data_fold() + f'/main_contracts.xlsx'

    @classmethod
    def paths_setting_jsonfile(cls):
        return cls.main_contract_data_fold() + f'/change_main_contract_path_setting.json'

    @classmethod
    def ensure_mainContractsFold_is_exist(cls):
        """
        Make sure main-contracts data fold is exist
        """
        if os.path.exists(path=cls.main_contract_data_fold()) is False:
            os.makedirs(cls.main_contract_data_fold())
