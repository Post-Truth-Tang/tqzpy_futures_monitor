import os
import datetime
import shutil

from vnpy.trader.tqz_extern.tools.file_path_operator.file_path_operator import TQZFilePathOperator


class TQZFutureMarketSedimentaryFundFilePath:

    @classmethod
    def futureMarketSedimentaryFund_data_fold(cls):
        return TQZFilePathOperator.current_file_father_path(file=__file__) + '/futureMarket_SedimentaryFund_data'

    @classmethod
    def futureMarketSedimentaryFund_excel_path(cls):
        return cls.futureMarketSedimentaryFund_data_fold() + f'/futureMarket_SedimentaryFund.xlsx'

    @classmethod
    def today_string(cls):
        return str(datetime.date.today())

    @classmethod
    def ensure_futureMarketSedimentaryFund_fold_is_exist(cls):
        """
        Make sure fold about future-market-fund is exist
        """

        if os.path.exists(cls.futureMarketSedimentaryFund_data_fold()) is False:
            os.makedirs(cls.futureMarketSedimentaryFund_data_fold())


class TQZAutoReportFilePath:

    @classmethod
    def autoReport_data_fold(cls):
        return TQZFilePathOperator.current_file_father_path(file=__file__) + '/auto_report_data'

    @classmethod
    def source_data_fold(cls):
        return cls.autoReport_data_fold() + '/source_data'

    @classmethod
    def output_data_fold(cls):
        return cls.autoReport_data_fold() + '/output_data'

    @classmethod
    def per_account_data_fold(cls):
        return cls.output_data_fold() + '/per_account_data'

    @classmethod
    def today_images_fold(cls):
        return cls.output_data_fold() + '/today_images'

    @classmethod
    def total_data_fold(cls):
        return cls.output_data_fold() + '/total_data'

    @classmethod
    def weekly_pdfs_fold(cls):
        return cls.output_data_fold() + '/weekly_pdfs'

    @classmethod
    def theory_source_data_excel_path(cls):
        if len(os.listdir(TQZAutoReportFilePath.source_data_fold())) > 1:
            raise Exception("error: source_data_fold have other file.")

        return cls.source_data_fold() + f'/source_data({cls.today_string()}).xlsx'

    @classmethod
    def current_source_data_excel_path(cls):
        if len(os.listdir(TQZAutoReportFilePath.source_data_fold())) > 1:
            raise Exception("error: source_data_fold have other file.")

        if len(os.listdir(TQZAutoReportFilePath.source_data_fold())) is 0:
            return ""

        for path in os.listdir(TQZAutoReportFilePath.source_data_fold()):
            return TQZAutoReportFilePath.source_data_fold() + f'/{path}'


    @classmethod
    def today_string(cls):
        return str(datetime.date.today())


    @classmethod
    def ensure_autoReportDataFold_is_exist(cls):
        """
        Make sure auto-report data fold is exist
        """

        if os.path.exists(path=cls.autoReport_data_fold()) is True:

            if os.path.exists(path=cls.source_data_fold()) is False:
                os.makedirs(cls.source_data_fold())

            if os.path.exists(path=cls.output_data_fold()) is False:
                os.makedirs(cls.output_data_fold())

                os.makedirs(cls.per_account_data_fold())
                os.makedirs(cls.today_images_fold())
                os.makedirs(cls.total_data_fold())
                os.makedirs(cls.weekly_pdfs_fold())

            elif os.path.exists(path=cls.output_data_fold()) is True:

                if os.path.exists(path=cls.per_account_data_fold()) is False:
                    os.makedirs(cls.per_account_data_fold())

                if os.path.exists(path=cls.today_images_fold()) is False:
                    os.makedirs(cls.today_images_fold())

                if os.path.exists(path=cls.total_data_fold()) is False:
                    os.makedirs(cls.total_data_fold())

                if os.path.exists(path=cls.weekly_pdfs_fold()) is False:
                    os.makedirs(cls.weekly_pdfs_fold())

        else:
            os.makedirs(cls.autoReport_data_fold())

            os.makedirs(cls.source_data_fold())
            os.makedirs(cls.output_data_fold())

            os.makedirs(cls.per_account_data_fold())
            os.makedirs(cls.today_images_fold())
            os.makedirs(cls.total_data_fold())
            os.makedirs(cls.weekly_pdfs_fold())


class TQZAutoReportFileCopyPath:

    @classmethod
    def auto_report_data_weixin_fold(cls):
        return TQZFilePathOperator.current_file_grandfather_path(
            file=TQZFilePathOperator.grandfather_path(source_path=__file__)
        ) + f'/.vntrader/auto_report_data_weixin'

    @classmethod
    def init_autoReportDataCopyFold(cls):
        """
        Init auto-report-data-copy fold.
        """

        if os.path.exists(path=cls.auto_report_data_weixin_fold()) is True:
            shutil.rmtree(cls.auto_report_data_weixin_fold())

        os.makedirs(cls.auto_report_data_weixin_fold())

    @classmethod
    def copy_data(cls, source_file, target_file):
        shutil.copy(src=source_file, dst=target_file)

