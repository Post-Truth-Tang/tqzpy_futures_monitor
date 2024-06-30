
from vnpy.gateway.rohon import RohonGateway
from vnpy.trader.future_gateway_login import TQZGatewayLogin

from vnpy.app.tqz_data_dump_app import TQZDataDumpApp

if __name__ == '__main__':
    TQZGatewayLogin(
        gateway=RohonGateway,
        init_strategies_seconds=60
    ).tqz_login_accounts(
        account_app_classes=[TQZDataDumpApp]
    )