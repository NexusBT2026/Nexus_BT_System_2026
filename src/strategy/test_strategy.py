"""
Test strategy for auto-detection demo.
"""

class TestStrategy:
    @staticmethod
    def populate_indicators(dataframe, metadata):
        # Dummy indicator
        dataframe['test_indicator'] = dataframe['close'] * 1.01
        return dataframe

    @staticmethod
    def populate_buy_trend(dataframe, metadata):
        # Dummy buy signal
        dataframe.loc[:, 'buy'] = dataframe['close'] > dataframe['open']
        return dataframe

    @staticmethod
    def populate_sell_trend(dataframe, metadata):
        # Dummy sell signal
        dataframe.loc[:, 'sell'] = dataframe['close'] < dataframe['open']
        return dataframe