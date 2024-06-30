
from vnpy.trader.tqz_extern.tqz_constant import *


# --- monitor web part ---
class TQZDropdownSelected(Enum):
    """
    Sort of Amonitor web.
    """

    NUMBER = "排序(序号)"
    BALANCE = "排序(动态权益)"
    RISKPERCENT = "排序(风险度)"
    PROFIT_AND_LOSS = "排序(当日盈亏)"


class TQZMonitorWebDataType(Enum):
    """
    Type of monitor web data
    """

    NUMBER = "序号"
    INVESTOR = "投资方"
    ACCOUNT_ID = "账户"
    BALANCE = "动态权益"
    USED_DEPOSIT = "已用保证金"
    PROFIT_AND_LOSS_TODAY = "当日盈亏"
    RISK_PERCENT = "风险度"



# --- future market sedimentary fund part ---
class TQZSedimentaryFundSheetType(Enum):
    """
    Sheet type of future-market-sedimentary-fund excel.
    """

    FUTURE_MARKET_SEDIMENTARY_FUND = "期货市场沉淀资金"


class TQZSedimentaryFundColumnType(Enum):
    """
    Column type of future-market-sedimentary-fund sheet.
    """

    DATE = "日期"
    SEDIMENTARY_FUND_TODAY = "当日沉淀资金"
    SEDIMENTARY_FUND_CHANGE = "沉淀资金变动"



# ----- auto report part -----
class TQZAutoReportSheetType(Enum):
    """
    Type of auto-report sheet name.
    """

    SOURCE_DATA = "当日数据源"
    PER_ACCOUNT_DATA = "单账户数据"
    BALANCE_TOTLE_FOLLOWING = "账户权益跟踪"


class TQZAutoReportPerAccountDataColumnType(Enum):
    """
    Type of auto-report(per account data) column name
    """

    DATE = "日期"

    BALANCE = "动态权益"
    SHARE = "份额"
    CURRENT_DAY_DEPOSIT = "当日入金"
    CURRENT_DAY_BONUS = "当日分红"
    CURRENT_DAY_TRANSFER = "当日出金"
    RESULT_PROFIT_AND_LOSS = "结算盈亏"
    NET_VALUE = "净值"
    MAX_DRAWDOWN = "最大回撤"

    BALANCE_FLUCTUATION_SINGLE_DAY = "单日权益波动"
    NET_VALUE_FLUCTUATION_SINGLE_DAY = "单日净值波动"
    AVERAGE_VOLATILITY_SINGLE_DAY = "单日平均波动率"

    NET_VALUE_ANNUALIZED = "年化净值"
    YIELD_RATE_ANNUALIZED = "年化收益率"

    YIELD_RATE_FLUCTUATION_STANDARD_DEVIATION = "收益率波动标准差"
    SHARPE_RATIO = "夏普比率"


class TQZAutoReportTotalBalanceFollowingColumnType(Enum):
    """
    Type of auto-report(total balance following) column name
    """

    DATE_ACCOUNT = "日期/账户"

    TOTAL_BALANCE = "总权益"
    PROFIT_AND_LOSS_TODAY = "当日盈亏"
    PROFIT_AND_LOSS_TODAY_PERCENT = "当日盈亏/总权益"

    PROFIT_AND_LOSS_TOTAL = "累计盈亏(当前)"
    PROFIT_AND_LOSS_TOTAL_HISTORY = "累计盈亏(历史)"

    SEDIMENTARY_FUND_TODAY = "当日沉淀资金(亿)"
    SEDIMENTARY_FUND_CHANGE = "沉淀资金变动(亿)"


class TQZAutoReportSourceDataColumnType(Enum):
    """
    Type of auto-report(source data) column name
    """

    ACCOUNT_NAME = "投资方"
    ACCOUNT_ID = "账户ID"
    ACCOUNT_BALANCE = "动态权益"
    ACCOUNT_RISK_PERCENT = "风险度"

    ACCOUNT_DEPOSIT = "当日入金(元)"
    ACCOUNT_TRANSFER = "当日出金(元)"
    ACCOUNT_BONUS = "当日分红(元)"
