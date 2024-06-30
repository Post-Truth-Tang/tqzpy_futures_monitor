
from vnpy.trader.tqz_extern.tqz_constant import *


# --- change main-contracts part ---
class TQZMainContractsColumnType(Enum):
    """
    Type of main-contracts excel column name
    """

    MAIN_CONTRACT = "主力合约"
    ENTRY_PRICE_HLA = "入场价格_HLA"
    STANDARD_LOTS_HLA = "标准手数_HLA"
    ENTRY_PRICE_HSR = "入场价格_HSR"


class TQZMainContractsSheetType(Enum):
    """
    Type of main-contracts sheet name.
    """

    CURRENT_FUTURE_MAIN_CONTRACT = "当前期货主力合约"


class TQZMainContractsStrategyPathType(Enum):
    """
    Type of strategy path which need change main contracts
    """

    CTA_STRATEGY_DATA_PATH = "cta_strategy_data_path"
    CTA_STRATEGY_SETTING_PATH = "cta_strategy_setting_path"
    PORTFOLIO_STRATEGY_DATA_PATH = "portfolio_strategy_data_path"
    PORTFOLIO_STRATEGY_SETTING_PATH = "portfolio_strategy_setting_path"


class TQZMainContractsKeyType(Enum):
    """
    Type of main-contracts key
    """

    MAIN_CONTRACT_KEY = "main_contract"
    POS_KEY = "pos"
    TARGET_POSITION_KEY = "target_position"
    ER_FACTOR_KEY = "er_factor"

    VT_SYMBOL_KEY = "vt_symbol"
    VT_SYMBOLS_KEY = "vt_symbols"

    ENTRY_PRICE_KEY = "entry_price"
    ENTRYPRICE_KEY = "entryprice"

    STANDARD_LOTS_KEY = "standard_lots_key"


class TQZCtaStrategyType(Enum):
    """
    Type of strategy
    """

    HLA_STRATEGY = "hla_strategy"
    HSR_STRATEGY = "hsr_strategy"

    PAIR_STRATEGY = "pair_strategy"
