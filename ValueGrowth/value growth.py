Python 3.7.0 (v3.7.0:1bf9cc5093, Jun 27 2018, 04:06:47) [MSC v.1914 32 bit (Intel)] on win32
Type "copyright", "credits" or "license()" for more information.
>>> # 导入函数库
from jqdata import *
import pandas as pd
import statsmodels.formula.api as sm
import numpy as np
import operator
import json

holding_number = 7

# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')
    
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    
    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
      # 开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 
      # 开盘时运行
    run_daily(market_open, time='open', reference_security='000300.XSHG')
      # 收盘后运行
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
    #每天持有最大股票数量
    
    
## 开盘前运行函数     
def before_market_open(context):
    # 输出运行时间
    log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))

## 开盘时运行函数
def market_open(context):
    
    #read_file()
    sellStockArr = json.loads(read_file('Sell_list').decode())
    buyStockArr = json.loads(read_file('Buy_list').decode())
        
    for stock in sellStockArr:
        order_target(stock, 0)
    
    # 计算卖出后拥有股票的数量
    current_stock_number = len(context.portfolio.positions)
    buy_stock_number = min(holding_number - current_stock_number, len(buyStockArr))
    log.info('buyStockArr: ' + str(buyStockArr))
    log.info('sellStockArr: ' + str(sellStockArr))
    log.info('current_stock_number: ' + str(current_stock_number))
    # 如果需要买入，则买入, 买入逻辑
    if buy_stock_number > 0:
        # portfolio的总cash
        cash = context.portfolio.cash
        value = context.portfolio.total_value
        # 每只股票的买入cash
        cash_per_stock = cash / buy_stock_number
        value_per_stock = value / holding_number
        # 如果一股超级贵，连一股都买不了怎么办？
        #for i in range(buy_stock_number):
            #order_target_value(buyStockArr[i], cash_per_stock)
        for i in range(buy_stock_number):
            order_target_value(buyStockArr[len(buyStockArr) - 1- i], cash_per_stock)
            
    log.info('调整后所拥有的positions: ' + str(context.portfolio.positions))
    
    

## 收盘后运行函数  
def after_market_close(context):
    log.info('一天结束')
    stocks = read_file("Universe02072019.txt").splitlines()
    stock_ratio_dict = {}
    sellStockArr = []
    buyStockArr = []
    
    for stock in stocks:
        calculate_stock_ratio(stock, context, stock_ratio_dict)
    
    # http://thomas-cokelaer.info/blog/2017/12/how-to-sort-a-dictionary-by-values-in-python/
    # 按照ratio从小到大排序
    sorted_dict = sorted(stock_ratio_dict.items(), key=operator.itemgetter(1))
    pointer = len(sorted_dict) - 1;

    log.info('调整前拥有的positions: ' + str(context.portfolio.positions))
    current_data = get_current_data()
    
    for (stock, ratio) in sorted_dict:
        if (pointer >= holding_number and stock in context.portfolio.positions):
            log.info('推荐卖出：' + stock);
            if current_data[stock].paused:
                log.info('停牌：' + stock);
                continue;
            sellStockArr.append(stock)
        if (pointer < holding_number and stock not in context.portfolio.positions and not current_data[stock].paused):
            log.info('推荐买入：' + stock);
            if current_data[stock].paused:
                log.info('停牌：' + stock);
                continue;
            buyStockArr.append(stock)
        pointer = pointer - 1  
        
    log.info(sellStockArr,buyStockArr)
    write_file('Buy_list', json.dumps(buyStockArr),append=False)
    write_file('Sell_list',json.dumps(sellStockArr), append=False)
    message = '推荐卖出：'+ str(sellStockArr) +'推荐买入：'+ str(buyStockArr)
    send_message(message, channel='weixin')
    
def calculate_stock_ratio(stock, context, stock_ratio_dict):
    # # 获取过去n天每天（frequency）收盘价格，从start_date到end_date。
    # prices = get_price(stock, start_date='2015-07-09', end_date='2017-08-09 23:00:00', frequency='daily', fields=['close'])
    # # 根据prices的个数得出交易日的序列号，从1到n
    # days = range(len(prices))
    
    # # 创建一个两列的dataframe，一列是收盘价格，另一列是交易日序列号
    # days_prices = {'prices':prices['close'].tolist(), 'days':days}
    # days_prices_dataframe = pd.DataFrame(days_prices)
    
    # # 做一条x为days，y为price的线
    # days_price_line = sm.ols(formula='prices ~ days', data=days_prices_dataframe).fit()
    start_date = get_security_info(stock).start_date
    
    days_price_line, days_prices_dataframe = get_line(stock, start_date, context.current_dt)
    
    # 把天数带入prices ~ days线，得出落在线上的价格，是一组数。
    prices_pred = days_price_line.predict(days_prices_dataframe["days"])  
    # 求出实际价格和线上价格的差的绝对值（residual），是一组数。
    residual = days_prices_dataframe["prices"].values - prices_pred
    residual = np.absolute(residual)
    # 从小到大进行排序
    residual.sort()
    # 求top 20%的residual的平均值，作为benchmark
    size = int(len(residual) * 0.2) * - 1
    top10PercentResidual = residual[size:] # :是从末尾取
    benchmark = top10PercentResidual.mean()
    #log.info(benchmark)
    
    # 求今天的交易日序列号
    days_from_start = get_trade_days(start_date)#??????????????????????????????????????????????????????????????????????
    curr_day = len(days_from_start) 

    # 这很傻逼。把今天的交易日序号做一个dictionary，然后构建一个dataframe，才能拿到今天的线上价格
    df = pd.DataFrame.from_dict({'days': [curr_day]})
    predicted_price_today = days_price_line.predict(df["days"]) 
    #log.info(predicted_price_today)
    
    # 获取今天开盘价格
    current_data = get_current_data()
    current_open_price = current_data[stock].day_open
    current_open_price = np.log(current_open_price)#?????????????????????
    
    residual_benchmark_ratio = 0
    # residual_benchmark_ratio越大，越应该买入
    # 如果当前开盘价格低于线上价格很多（超过benchmark），加入dict
    # 如过持有当前股票，那么也要加入dict，这只股票的ratio可能是负数
    if ((predicted_price_today[0] - current_open_price > benchmark) or
    (stock in context.portfolio.positions)):
        residual_benchmark_ratio = (predicted_price_today[0] - current_open_price) / benchmark
        stock_ratio_dict[stock] = residual_benchmark_ratio

def get_line(stock, start_date, end_date):
    # 获取过去n天价格
    #prices_full = get_price(stock, start_date=start_date, end_date=end_date, frequency='daily', fields=['close'])
    
    prices1 = get_price(stock, start_date=start_date, end_date='2015-03-01', frequency='daily', fields=['close'])
    days1 = range(len(prices1))
    
    prices2 = get_price(stock, start_date='2016-03-01', end_date=end_date, frequency='daily', fields=['close'])
    days_after_gap = len(get_trade_days(start_date=start_date, end_date='2016-03-01'))
    days2 = range(days_after_gap, days_after_gap + len(prices2))
    
    prices = prices1.append(prices2)
    #get log prices
    prices = np.log(prices) #????????????????????????????????????????
    
    days = days1 + days2
    days_prices = {'prices':prices['close'].tolist(), 'days':days}
    days_prices_dataframe = pd.DataFrame(days_prices)
    #print(days_prices_dataframe)
    days_prices_dataframe = days_prices_dataframe.dropna()
    
    #OLS
    days_price_line = sm.ols(formula='prices ~ days', data=days_prices_dataframe).fit()
    return days_price_line, days_prices_dataframe
    
    log.info('##############################################################')
