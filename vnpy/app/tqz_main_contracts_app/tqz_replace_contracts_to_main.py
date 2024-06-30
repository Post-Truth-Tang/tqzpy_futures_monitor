import pandas
import re

from vnpy.trader.tqz_extern.tools.position_operator.position_operator import TQZJsonOperator
from vnpy.trader.tqz_extern.tools.symbol_operator.symbol_operator import TQZSymbolOperator
from vnpy.app.tqz_main_contracts_app.main_contracts_data_file_path import TQZMainContractsChangeFilePath
from vnpy.trader.tqz_extern.tools.pandas_operator.pandas_operator import TQZPandas
TQZPandas.pre_set()

from vnpy.app.tqz_main_contracts_app.tqz_constant import (
    TQZMainContractsSheetType,
    TQZMainContractsColumnType,
    TQZMainContractsStrategyPathType,
    TQZMainContractsKeyType,
    TQZCtaStrategyType
)

class TQZReplaceContractsToMain:

    @classmethod
    def tqz_replace_contracts_to_main(cls):
        """
        Replace excel data to main contracts data
        """

        paths_setting_content = TQZJsonOperator.tqz_load_jsonfile(
            jsonfile=TQZMainContractsChangeFilePath.paths_setting_jsonfile()
        )

        [cls.__reset_main_contracts(
            strategy_type=strategy_type,
            strategy_type_data=strategy_type_data
        ) for strategy_type, strategy_type_data in paths_setting_content.items()]
        print("主力合约 更换完毕")

    @staticmethod
    def __get_main_contracts_dictionary(cta_strategy_type: TQZCtaStrategyType):
        """
        Change main_contracts format from dataframe to dictionary and return dictionary
        """

        main_contracts_dataframe = pandas.read_excel(
            io=TQZMainContractsChangeFilePath.main_contracts_excel(),
            sheet_name=TQZMainContractsSheetType.CURRENT_FUTURE_MAIN_CONTRACT.value
        )

        if cta_strategy_type == TQZCtaStrategyType.HLA_STRATEGY:
            main_contracts_dataframe.dropna(subset=[TQZMainContractsColumnType.ENTRY_PRICE_HLA.value, TQZMainContractsColumnType.STANDARD_LOTS_HLA.value], inplace=True)
        elif cta_strategy_type == TQZCtaStrategyType.HSR_STRATEGY:
            main_contracts_dataframe.dropna(subset=[TQZMainContractsColumnType.ENTRY_PRICE_HSR.value], inplace=True)
        elif cta_strategy_type == TQZCtaStrategyType.PAIR_STRATEGY:
            main_contracts_dataframe.set_index(TQZMainContractsColumnType.MAIN_CONTRACT.value, inplace=True)
            main_contracts_dataframe.dropna(axis=0, how='all', inplace=True)
            main_contracts_dataframe.reset_index(inplace=True)

        main_contracts_dictionary = {}
        for index in main_contracts_dataframe.index:
            main_contract = main_contracts_dataframe.loc[index][TQZMainContractsColumnType.MAIN_CONTRACT.value]
            standard_lots = main_contracts_dataframe.loc[index][TQZMainContractsColumnType.STANDARD_LOTS_HLA.value]
            sym = re.match(r"^[a-zA-Z]{1,3}", main_contract.split(".")[0]).group()

            if cta_strategy_type == TQZCtaStrategyType.HLA_STRATEGY:
                entry_price = main_contracts_dataframe.loc[index][TQZMainContractsColumnType.ENTRY_PRICE_HLA.value]
                main_contracts_dictionary[sym] = {
                    TQZMainContractsKeyType.MAIN_CONTRACT_KEY.value: main_contract,
                    TQZMainContractsKeyType.ENTRY_PRICE_KEY.value: float(entry_price),
                    TQZMainContractsKeyType.STANDARD_LOTS_KEY.value: int(standard_lots)
                }
            elif cta_strategy_type == TQZCtaStrategyType.HSR_STRATEGY:
                entry_price = main_contracts_dataframe.loc[index][TQZMainContractsColumnType.ENTRY_PRICE_HSR.value]
                main_contracts_dictionary[sym] = {
                    TQZMainContractsKeyType.MAIN_CONTRACT_KEY.value: main_contract,
                    TQZMainContractsKeyType.ENTRY_PRICE_KEY.value: float(entry_price)
                }
            elif cta_strategy_type == TQZCtaStrategyType.PAIR_STRATEGY:
                main_contracts_dictionary[sym] = {
                    TQZMainContractsKeyType.MAIN_CONTRACT_KEY.value: main_contract
                }

        return main_contracts_dictionary

    @classmethod
    def __reset_main_contracts(cls, strategy_type, strategy_type_data):

        if TQZMainContractsStrategyPathType.CTA_STRATEGY_DATA_PATH.value == strategy_type:

            [cls.__reset_cta_strategy_data_main_contracts(
                cta_data_path=cta_data_path,
                cta_strategy_type=TQZCtaStrategyType.HLA_STRATEGY
            ) for cta_data_path in strategy_type_data[TQZCtaStrategyType.HLA_STRATEGY.value].values()]

            [cls.__reset_cta_strategy_data_main_contracts(
                cta_data_path=cta_data_path,
                cta_strategy_type=TQZCtaStrategyType.HSR_STRATEGY
            ) for cta_data_path in strategy_type_data[TQZCtaStrategyType.HSR_STRATEGY.value].values()]

        elif TQZMainContractsStrategyPathType.CTA_STRATEGY_SETTING_PATH.value == strategy_type:

            [cls.__reset_cta_strategy_setting_main_contracts(
                cta_setting_path=cta_setting_path,
                cta_strategy_type=TQZCtaStrategyType.HLA_STRATEGY
            ) for cta_setting_path in strategy_type_data[TQZCtaStrategyType.HLA_STRATEGY.value].values()]

            [cls.__reset_cta_strategy_setting_main_contracts(
                cta_setting_path=cta_setting_path,
                cta_strategy_type=TQZCtaStrategyType.HSR_STRATEGY
            ) for cta_setting_path in strategy_type_data[TQZCtaStrategyType.HSR_STRATEGY.value].values()]

        elif TQZMainContractsStrategyPathType.PORTFOLIO_STRATEGY_DATA_PATH.value == strategy_type:

            [cls.__reset_portfolio_strategy_data_main_contracts(
                portfolio_strategy_data_path=portfolio_strategy_data_path
            ) for portfolio_strategy_data_path in strategy_type_data.values()]

        elif TQZMainContractsStrategyPathType.PORTFOLIO_STRATEGY_SETTING_PATH.value == strategy_type:

            [cls.__reset_portfolio_strategy_setting_main_contracts(
                portfolio_strategy_setting_path=portfolio_strategy_setting_path
            ) for portfolio_strategy_setting_path in strategy_type_data.values()]


    @classmethod
    def __reset_cta_strategy_data_main_contracts(cls, cta_data_path, cta_strategy_type: TQZCtaStrategyType):
        """
        Reset main contracts of cta strategy data.
        """

        main_contracts_dictionary = cls.__get_main_contracts_dictionary(cta_strategy_type=cta_strategy_type)

        cta_strategy_data_before = TQZJsonOperator.tqz_load_jsonfile(jsonfile=cta_data_path)
        cta_strategy_data_after = {}

        for vt_symbol_strategy, vt_symbol_strategy_content in cta_strategy_data_before.items():
            sym = TQZSymbolOperator.get_sym(vt_symbol=vt_symbol_strategy)

            if sym in main_contracts_dictionary.keys():
                current_main_contract = main_contracts_dictionary[sym][TQZMainContractsKeyType.MAIN_CONTRACT_KEY.value]
                strategy = vt_symbol_strategy.split(".")[2]
                new_vt_symbol_strategy = f'{current_main_contract}.{strategy}'
                vt_symbol_strategy_content[TQZMainContractsKeyType.ENTRYPRICE_KEY.value] = main_contracts_dictionary[sym][TQZMainContractsKeyType.ENTRY_PRICE_KEY.value]

                cta_strategy_data_after[new_vt_symbol_strategy] = vt_symbol_strategy_content
            else:
                cta_strategy_data_after[vt_symbol_strategy] = vt_symbol_strategy_content

        TQZJsonOperator.tqz_write_jsonfile(content=cta_strategy_data_after, target_jsonfile=cta_data_path)

    @classmethod
    def __reset_cta_strategy_setting_main_contracts(cls, cta_setting_path, cta_strategy_type: TQZCtaStrategyType):
        """
        Reset main contracts of cta strategy setting.
        """

        main_contracts_dictionary = cls.__get_main_contracts_dictionary(cta_strategy_type=cta_strategy_type)

        cta_strategy_setting_before = TQZJsonOperator.tqz_load_jsonfile(jsonfile=cta_setting_path)
        cta_strategy_setting_after = {}

        for vt_symbol_strategy, vt_symbol_strategy_content in cta_strategy_setting_before.items():
            sym = TQZSymbolOperator.get_sym(vt_symbol=vt_symbol_strategy)

            if sym in main_contracts_dictionary.keys():
                current_main_contract = main_contracts_dictionary[sym][TQZMainContractsKeyType.MAIN_CONTRACT_KEY.value]
                strategy = vt_symbol_strategy.split(".")[2]
                new_vt_symbol_strategy = f'{current_main_contract}.{strategy}'

                vt_symbol_strategy_content[TQZMainContractsKeyType.VT_SYMBOL_KEY.value] = current_main_contract

                cta_strategy_setting_after[new_vt_symbol_strategy] = vt_symbol_strategy_content
            else:
                cta_strategy_setting_after[vt_symbol_strategy] = vt_symbol_strategy_content

        TQZJsonOperator.tqz_write_jsonfile(content=cta_strategy_setting_after, target_jsonfile=cta_setting_path)

    @classmethod
    def __reset_portfolio_strategy_data_main_contracts(cls, portfolio_strategy_data_path):
        """
        Reset main contracts of portfolio strategy data.
        """

        main_contracts_dictionary = cls.__get_main_contracts_dictionary(cta_strategy_type=TQZCtaStrategyType.PAIR_STRATEGY)

        portfolio_strategy_data_before = TQZJsonOperator.tqz_load_jsonfile(jsonfile=portfolio_strategy_data_path)
        portfolio_strategy_data_after = {}

        for sym_pair, sym_pair_content in portfolio_strategy_data_before.items():
            portfolio_strategy_data_after[sym_pair] = {}

            for inside_key, inside_data in sym_pair_content.items():
                portfolio_strategy_data_after[sym_pair][inside_key] = {}

                if TQZMainContractsKeyType.POS_KEY.value == inside_key:
                    for inside_vt_symbol, inside_vt_symbol_pos in inside_data.items():
                        inside_sym = TQZSymbolOperator.get_sym(vt_symbol=inside_vt_symbol)

                        if inside_sym in main_contracts_dictionary.keys():
                            current_main_contract = main_contracts_dictionary[inside_sym][TQZMainContractsKeyType.MAIN_CONTRACT_KEY.value]
                            portfolio_strategy_data_after[sym_pair][inside_key][current_main_contract] = inside_vt_symbol_pos
                        else:
                            portfolio_strategy_data_after[sym_pair][inside_key][inside_vt_symbol] = inside_vt_symbol_pos

                elif TQZMainContractsKeyType.TARGET_POSITION_KEY.value == inside_key:
                    for inside_vt_symbol, inside_vt_symbol_pos in inside_data.items():
                        inside_sym = TQZSymbolOperator.get_sym(vt_symbol=inside_vt_symbol)

                        if inside_sym in main_contracts_dictionary.keys():
                            current_main_contract = main_contracts_dictionary[inside_sym][TQZMainContractsKeyType.MAIN_CONTRACT_KEY.value]
                            portfolio_strategy_data_after[sym_pair][inside_key][current_main_contract] = inside_vt_symbol_pos
                        else:
                            portfolio_strategy_data_after[sym_pair][inside_key][inside_vt_symbol] = inside_vt_symbol_pos
                elif TQZMainContractsKeyType.ER_FACTOR_KEY.value == inside_key:
                    for inside_vt_symbol, inside_vt_symbol_pos in inside_data.items():
                        inside_sym = TQZSymbolOperator.get_sym(vt_symbol=inside_vt_symbol)

                        if inside_sym in main_contracts_dictionary.keys():
                            current_main_contract = main_contracts_dictionary[inside_sym][TQZMainContractsKeyType.MAIN_CONTRACT_KEY.value]
                            portfolio_strategy_data_after[sym_pair][inside_key][current_main_contract] = inside_vt_symbol_pos
                        else:
                            portfolio_strategy_data_after[sym_pair][inside_key][inside_vt_symbol] = inside_vt_symbol_pos
                else:
                    portfolio_strategy_data_after[sym_pair][inside_key] = inside_data

        TQZJsonOperator.tqz_write_jsonfile(
            content=portfolio_strategy_data_after,
            target_jsonfile=portfolio_strategy_data_path
        )

    @classmethod
    def __reset_portfolio_strategy_setting_main_contracts(cls, portfolio_strategy_setting_path):
        """
        Reset main contracts of portfolio strategy setting
        """

        main_contracts_dictionary = cls.__get_main_contracts_dictionary(cta_strategy_type=TQZCtaStrategyType.PAIR_STRATEGY)

        portfolio_strategy_setting_before = TQZJsonOperator.tqz_load_jsonfile(jsonfile=portfolio_strategy_setting_path)
        portfolio_strategy_setting_after = {}

        for sym_pair, sym_pair_content in portfolio_strategy_setting_before.items():
            portfolio_strategy_setting_after[sym_pair] = {}

            for inside_key, inside_data in sym_pair_content.items():
                portfolio_strategy_setting_after[sym_pair][inside_key] = {}

                if TQZMainContractsKeyType.VT_SYMBOLS_KEY.value == inside_key:
                    temp_inside_data = []
                    for vt_symbol in inside_data:
                        temp_sym = TQZSymbolOperator.get_sym(vt_symbol=vt_symbol)

                        if temp_sym in main_contracts_dictionary.keys():
                            current_main_contract = main_contracts_dictionary[temp_sym][TQZMainContractsKeyType.MAIN_CONTRACT_KEY.value]
                            temp_inside_data.append(current_main_contract)
                        else:
                            temp_inside_data.append(vt_symbol)

                    portfolio_strategy_setting_after[sym_pair][inside_key] = temp_inside_data
                else:
                    portfolio_strategy_setting_after[sym_pair][inside_key] = inside_data

        TQZJsonOperator.tqz_write_jsonfile(
            content=portfolio_strategy_setting_after,
            target_jsonfile=portfolio_strategy_setting_path
        )


if __name__ == '__main__':
    TQZReplaceContractsToMain.tqz_replace_contracts_to_main()