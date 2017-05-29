# 导入聚宽函数库
import jqdata
import scipy.stats as stats
import numpy as np
import pandas as pd
from pandas import DataFrame,Series
import statsmodels
from statsmodels.tsa.stattools import coint
from datetime import timedelta
from datetime import datetime
import statsmodels.tsa.stattools as sts
import operator
import datetime as dt
from dateutil import relativedelta
from jqdata import *


# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    set_slippage(PriceRelatedSlippage(0.01))
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')
    g.back_test_period = 30
    g.day_count = 0
    g.stockList = None
    g.adfTest_period = 1500
    g.alpha_index = 2
    g.beta_index = 3
    g.Y_stock_index = 1
    g.X_stock_index = 0
    g.spread_std_index = 4
    g.spread_mean_index = 5
    g.in_trend_days = 5
    g.avoid_market_risk = None
    g.MF_period = 3
    g.high_weight_stocks = ['601318.XSHG', '600036.XSHG','600016.XSHG', '601166.XSHG',
        '600000.XSHG', '600030.XSHG', '000002.XSHE', '600837.XSHG', '600519.XSHG', '000651.XSHE',
        '601328.XSHG', '600887.XSHG', '601288.XSHG', '601601.XSHG','601398.XSHG']
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    
    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
      # 开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 
      # 开盘时运行
    run_daily(market_open, time='every_bar', reference_security='000300.XSHG')
      # 收盘后运行
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
    
class stock_cointergration():
    def __init__(self):
        pass
    
    def Do_hedge(self, pair,context):
        print ('pair is ', pair)
        stockX = pair[g.X_stock_index]
        stockY = pair[g.Y_stock_index]
        beta = pair[g.beta_index]
        alpha = pair[g.alpha_index]
        spread_mean = pair[g.spread_mean_index]
        spread_std = pair[g.spread_std_index]
        df= history(1, unit='1m', field='close', security_list=[stockX, stockY], df=True, skip_paused=False, fq='pre')
        stockX_price = df[stockX][0]
        stockY_price = df[stockY][0]
        spread = stockY_price - stockX_price*beta
        # spread = (float)(spread - spread_mean)/spread_std
        # if spread > 2 and spread < 4:
        #     if stockY in context.portfolio.positions:
        #         order_target(stockY, 0)
        #     target_value = context.portfolio.portfolio_value
        #     order_target_value(stockX, target_value)
        # if spread < -2 and spread > -4:
        #     if stockX in context.portfolio.positions:
        #         order_target(stockX, 0)
        #     target_value = context.portfolio.portfolio_value
        #     order_target_value(stockY, target_value)
        # if spread > 4 or spread < -4 or spread < 0.3 and spread > -0.3:
        #     order_target(stockX, 0)
        #     order_target(stockY, 0)
        if spread > 2*spread_std and spread < 4*spread_std:
            if stockY in context.portfolio.positions:
                order_target(stockY, 0)
            target_value = context.portfolio.portfolio_value
            order_target_value(stockX, target_value)
        if spread < -2*spread_std and spread > -4*spread_std:
            if stockX in context.portfolio.positions:
                order_target(stockX, 0)
            target_value = context.portfolio.portfolio_value
            order_target_value(stockY, target_value)
        if spread > 4*spread_std or spread < -4*spread_std or spread < 0.3*spread_std and spread > -0.3*spread_std:
            order_target(stockX, 0)
            order_target(stockY, 0)
            
                
        
    def find_cointergrate_stocks(self,stockList):
        stocks_pair = {}
        price_df = history(g.adfTest_period, unit='1d', field='close', security_list=stockList, df=True, skip_paused=False, fq='pre')
        for i in range(len(stockList)):
            stock1 =  stockList[i]
            stock1_price = price_df[stock1]
            for j in range(i+1,len(stockList)):
                stock2 = stockList[j]
                stock2_price =  price_df[stock2]
                combined_df = pd.concat([stock1_price,stock2_price],axis=1)
                print ('combined_df is ', combined_df)
                combined_df = combined_df.dropna()
                if len(combined_df) < 500:
                    continue
                model = pd.ols(y=stock2_price, x=stock1_price, intercept=True)   # perform ols on these two stocks
                spread = stock2_price - stock1_price*model.beta['x']
                spread = spread.dropna()
                spread = spread.values
                sta = sts.adfuller(spread, 1)
                if sta[1] < 0.05 and sta[0] < sta[4]['5%'] and model.beta['x'] > 0:
                    stocks_pair[(stock1,stock2, model.beta[1], model.beta['x'],np.std(spread), np.mean(spread))] = sta[0]
        rank = sorted(stocks_pair.items(),key=operator.itemgetter(1))
        return rank[:1]


class market_risk_control():
    def __init__(self):
        return          
    
    def avoid_market_rist_MF(self,stock_list, context):
        delta = relativedelta.relativedelta(days=-1)
        dt = context.current_dt + delta
        money_df = get_money_flow(stock_list,  end_date=dt, fields=['net_amount_main', 'sec_code'], count= g.MF_period)
        money_series =  money_df['net_amount_main']
        money_df.drop('sec_code',1, inplace=True)
        days_money_trend = []
        for i in range(g.MF_period):
            days_money_trend.append(money_series.iloc[i::g.MF_period].sum())
        for money_flow in days_money_trend:
            if money_flow > 0:
                return False
        return True
        
## 开盘前运行函数     
def before_market_open(context):
    # 输出运行时间
    log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))
    
    
    # 给微信发送消息（添加模拟交易，并绑定微信生效）
    send_message('美好的一天~')

    # 要操作的股票：平安银行（g.为全局变量）
    #801780 HY008
    #stockList = get_industry_stocks('C25', date=None)
    #print ('stockList is ', stockList)
    
    # stockList = ['000059.XSHE', '000637.XSHE', '000698.XSHE', '000723.XSHE', '000819.XSHE', '000835.XSHE', 
    # '002377.XSHE', '002778.XSHE', '600179.XSHG', '600281.XSHG', '600688.XSHG', '600721.XSHG', '600725.XSHG', 
    # '600740.XSHG', '600792.XSHG', '600997.XSHG', '601011.XSHG', '601015.XSHG', '603798.XSHG']
    
    stockList = ['000001.XSHE', '002142.XSHE', '600000.XSHG', '600015.XSHG', '600016.XSHG', 
    '600036.XSHG', '601009.XSHG', '601166.XSHG', '601169.XSHG', '601288.XSHG', '601328.XSHG', 
    '601398.XSHG', '601818.XSHG', '601939.XSHG', '601988.XSHG', '601998.XSHG']
    
    #process_stocks_obj = process_stocks(stockList)
    #proper_stocks = process_stocks_obj.get_proper_stocks(context)
    #print ('proper_stocks length is ', len(proper_stocks))
    context.stock_cointergration_obj = stock_cointergration()
    market_risk_control_obj = market_risk_control()
    if g.day_count == 0:
        context.stock_pair = context.stock_cointergration_obj.find_cointergrate_stocks(stockList)[0][0]
    g.day_count += 1
    g.day_count = g.day_count%g.back_test_period
    #g.avoid_market_risk = market_risk_control_obj.avoid_market_rist_MF(g.high_weight_stocks,context)
## 开盘时运行函数
def market_open(context):
    log.info('函数运行时间(market_open):'+str(context.current_dt.time()))
    # if g.avoid_market_risk:
    #     for stock in context.portfolio.positions:
    #         order_target(stock, 0)
    # else:
    context.stock_cointergration_obj.Do_hedge(context.stock_pair, context)
 
## 收盘后运行函数  
def after_market_close(context):
    log.info(str('函数运行时间(after_market_close):'+str(context.current_dt.time())))
    #得到当天所有成交记录
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：'+str(_trade))
    log.info('一天结束')
    log.info('##############################################################')
