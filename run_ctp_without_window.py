
from vnpy.gateway.ctp import CtpGateway
from vnpy.trader.future_gateway_login import TQZGatewayLogin

from vnpy.app.cta_strategy import CtaStrategyApp

if __name__ == '__main__':
    TQZGatewayLogin(
        gateway=CtpGateway,
        init_strategies_seconds=60
    ).tqz_login_accounts(
        account_app_classes=[CtaStrategyApp]
    )