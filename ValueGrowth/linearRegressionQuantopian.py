"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
import quantopian.algorithm as algo
from quantopian.pipeline import CustomFactor, CustomFilter, Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters import QTradableStocksUS
import pandas as pd
import statsmodels.api as sm
import numpy as np
import operator

# class SidInList(CustomFilter):
#     """
#     Filter returns True for any SID included in parameter tuple passed at creation.
#     Usage: my_filter = SidInList(sid_list=(23911, 46631))
#     """    
#     inputs = []
#     window_length = 1
#     params = ('sid_list',)

#     def compute(self, today, assets, out, sid_list):
#         out[:] = np.in1d(assets, sid_list)       
 

def train_model(price_history):
    # 获取过去n天价格
    days = range(len(price_history))
    time_constant_independent_variable = sm.add_constant(days)
    model = sm.OLS(price_history,time_constant_independent_variable)
    results= model.fit()
    return results, time_constant_independent_variable
    
def calculate_stock_ratio(stock, context, data, stock_ratio_dict):
    # # 获取过去n天每天（frequency）收盘价格，从start_date到end_date。
    # prices = get_price(stock, start_date='2015-07-09', end_date='2017-08-09 23:00:00', frequency='daily', fields=['close'])
    # # 根据prices的个数得出交易日的序列号，从1到n
    price_history_current_series = data.history(stock, 'price', context.look_back_date + 1, '1d')
    price_history = np.log(price_history_current_series.iloc[0:(len(price_history_current_series)-1)])
    price_current = np.log(price_history_current_series.iloc[-1])
    
    current_date_number = [len(price_history_current_series)]

    current_date_variable = sm.add_constant(current_date_number,has_constant='add')
    
    # # 做一条x为days，y为price的线
    days_price_model, time_constant_independent_variable = train_model(price_history)
    prices_pred = days_price_model.predict(time_constant_independent_variable)  
    # 求出实际价格和线上价格的差的绝对值（residual），是一组数。
    residual = price_history.values - prices_pred
    residual = np.absolute(residual)

    # 从小到大进行排序
    residual.sort()
    # 求top 20%的residual的平均值，作为benchmark
    size = int(len(residual) * 0.2) * - 1
    top10PercentResidual = residual[size:] # :是从末尾取
    benchmark = top10PercentResidual.mean()
    #log.info(benchmark)
    # 求今天的交易日序列号

    predicted_price_today = days_price_model.predict(current_date_variable) 

    residual_benchmark_ratio = 0
    # residual_benchmark_ratio越大，越应该买入
    # 如果当前开盘价格低于线上价格很多（超过benchmark），加入dict
    # 如过持有当前股票，那么也要加入dict，这只股票的ratio可能是负数

    if ((predicted_price_today[0] - price_current > benchmark) or
    (stock in context.portfolio.positions)):
        residual_benchmark_ratio = (predicted_price_today[0] - price_current) / benchmark
        stock_ratio_dict[stock] = residual_benchmark_ratio
        
    
# built customized filter
#https://www.quantopian.com/posts/using-a-specific-list-of-securities-in-pipeline#57964b09938eade52300015b
# class LinearRegression(CustomerFactor):
#     #Fundamentals.ipo_date
#     #inputs =[USEquityPricing.close]
#     inputs = [Fundamentals.ipo_date]
#     def compute(self, today, assets, out, close):
#         current_date = str(get_datetime().date()) 
#         out[:] = np.log(close);
        
        
def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    context.holding_number = 7
    context.sellStockArr = []
    context.buyStockArr = []
    set_symbol_lookup_date('2016-1-1')
    context.sid_list = [
            symbol('AAPL'), 
            symbol('AMZN'),
            symbol('SQ'),
            symbol('AFT'), 
            symbol('ARDC'),
            symbol('ACP'),
            symbol('BHL'),
            symbol('FRA'),
            symbol('BGT'),
            symbol('BSL'),
            symbol('BGX'),
            symbol('BGB'),
            symbol('EFT'),
            symbol('EFF'),
            symbol('EFR'),
            symbol('EVF'),
            symbol('FCT'),
            symbol('VVR'),
            symbol('VTA'),
            symbol('JQC'),
            symbol('JRO'),
            symbol('JFR'),
               ]
    context.look_back_date = 300
    # pipe = make_pipeline()
    # # pipe.add(my_factor, 'my_factor')
    # algo.attach_pipeline(pipe, 'linear_regression')
    
    # Rebalance every day, 1 hour after market open.
    algo.schedule_function(
        rebalance,
        algo.date_rules.every_day(),
        algo.time_rules.market_open(hours=0, minutes=1),
    )

    # Record tracking variables at the end of each day.
    algo.schedule_function(
        process_price_model,
        algo.date_rules.every_day(),
        algo.time_rules.market_close(hours=0, minutes=1),
    )

# def make_pipeline():
#     """
#     A function to create our dynamic stock selector (pipeline). Documentation
#     on pipeline can be found here:
#     https://www.quantopian.com/help#pipeline-title
#     """
#     # set_symbol_lookup_date('2016-1-1')
#     # my_sid_filter = SidInList(
#     #     sid_list = (
#     #         symbol('AFT').sid, 
#     #         symbol('ARDC').sid,
#     #         symbol('ACP').sid,
#     #         symbol('BHL').sid,
#     #         symbol('FRA').sid,
#     #         symbol('BGT').sid,
#     #         symbol('BSL').sid,
#     #         symbol('BGX').sid,
#     #         symbol('BGB').sid,
#     #         symbol('EFT').sid,
#     #         symbol('EFF').sid,
#     #         symbol('EFR').sid,
#     #         symbol('EVF').sid,
#     #         symbol('FCT').sid,
#     #         symbol('VVR').sid,
#     #         symbol('VTA').sid,
#     #         symbol('JQC').sid,
#     #         symbol('JRO').sid,
#     #         symbol('JFR').sid,
#     #         symbol('NSL').sid,
#     #         symbol('JSD').sid,
#     #         symbol('OXLC').sid,
#     #         symbol('TSLF').sid,
#     #         symbol('PPR').sid,
#     #         symbol('PHD').sid,
#     #         symbol('TLI').sid,
#     #             )
#     #         )
#     # Base universe set to the QTradableStocksUS
#     # base_universe = context.assets
#     # price_history = data.history(base_universe, fields = 'close', bar_count = 2000, frequency='1d')
#     #QTradableStocksUS()
#     linear_regression_factor = LinearRegression(window_length=205)
#     linear_regression_factor = linear_regression_factor.linear_regression(target=returns_slice, regression_length=200)
    
#     # Factor of yesterday's close price.
#     #yesterday_close = USEquityPricing.close.latest

#     pipe = Pipeline(
#         columns={
#             'linear_regression_factor': linear_regression_factor,
#         },
#         screen=my_sid_filter
#     )
#     return pipe


# def before_trading_start(context, data):
#     """
#     Called every day before market open.
#     """
#     context.output = algo.pipeline_output('linear_regression')
#     log.info(context.output.head())


#     # These are the securities that we are interested in trading each day.
#     context.security_list = context.output.index


def rebalance(context, data):
    """
    Execute orders according to our schedule_function() timing.
    """
    #read_file()
        
    for stock in context.sellStockArr:
        order_target(stock, 0)
    
    # 计算卖出后拥有股票的数量
    current_stock_number = len(context.portfolio.positions)
    buy_stock_number = min(context.holding_number - current_stock_number, len(context.buyStockArr))
    
    # 如果需要买入，则买入, 买入逻辑
    if buy_stock_number > 0:
        # portfolio的总cash
        cash = context.portfolio.cash
        value = context.portfolio.portfolio_value
        # 每只股票的买入cash
        cash_per_stock = cash / buy_stock_number
        value_per_stock = value / context.holding_number
        # 如果一股超级贵，连一股都买不了怎么办？
        #for i in range(buy_stock_number):
            #order_target_value(buyStockArr[i], cash_per_stock)
        for i in range(buy_stock_number):
            order_target_value(context.buyStockArr[i], cash_per_stock)
            
    log.info('调整后所拥有的positions: ' + str(context.portfolio.positions))
    pass


def process_price_model(context, data):
    """
    Plot variables at the end of each day.
    
    """
    stocks = context.sid_list
    #read_file("Universe02072019.txt").splitlines()
    stock_ratio_dict = {}
    sellStockArr = []
    buyStockArr = []
    
    for stock in stocks:
        calculate_stock_ratio(stock, context, data, stock_ratio_dict)
    log.info('stock_ratio_dict is ' + str(stock_ratio_dict))
    # http://thomas-cokelaer.info/blog/2017/12/how-to-sort-a-dictionary-by-values-in-python/
    # 按照ratio从小到大排序
    sorted_dict = sorted(stock_ratio_dict.items(), key=operator.itemgetter(1))
    pointer = len(sorted_dict) - 1;

    log.info('current positions ' + str(context.portfolio.positions))
    for (stock, ratio) in sorted_dict:
        if (pointer >= context.holding_number and stock in context.portfolio.positions):
            log.info('sell ' + str(stock));
            if not data.can_trade(stock):
                log.info('suspend ' + str(stock));
                continue;
            sellStockArr.append(stock)
        if (pointer < context.holding_number and stock not in context.portfolio.positions and  data.can_trade(stock)):
            log.info('buy stock' + str(stock));
            if not data.can_trade(stock):
                log.info('suspend ' + str(stock));
                continue;
            buyStockArr.append(stock)
        pointer = pointer - 1  
        
    log.info(sellStockArr,buyStockArr)
    context.sellStockArr = sellStockArr
    context.buyStockArr = buyStockArr
    pass


def handle_data(context, data):
    """
    Called every minute.
    """
    pass