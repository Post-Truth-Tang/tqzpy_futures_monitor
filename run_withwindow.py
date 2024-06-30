# flake8: noqa

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy.gateway.ctp import CtpGateway
# from vnpy.gateway.rohon import RohonGateway
# from vnpy.gateway.epi import EpiGateway
# from vnpy.gateway.jees import jeesGateway
# from vnpy.gateway.qjn.qjn_gateway import QjnGateway

# from vnpy.app.position_manager import PositionManagerApp
# from vnpy.app.cta_strategy import CtaStrategyApp
from vnpy.app.tqz_data_dump_app import TQZDataDumpApp


def main():
    """"""

    qapp = create_qapp()

    event_engine = EventEngine()

    main_engine = MainEngine(event_engine)

    # -------------------------------------------------------------

    main_engine.add_gateway(gateway_class=CtpGateway)
    # main_engine.add_gateway(gateway_class=RohonGateway)
    # main_engine.add_gateway(gateway_class=EpiGateway)
    # main_engine.add_gateway(gateway_class=jeesGateway)
    # main_engine.add_gateway(gateway_class=QjnGateway)

    # main_engine.add_app(app_class=PositionManagerApp)
    # main_engine.add_app(app_class=CtaStrategyApp)
    main_engine.add_app(app_class=TQZDataDumpApp)

    # -------------------------------------------------------------


    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()
    qapp.exec()

if __name__ == "__main__":
    main()
