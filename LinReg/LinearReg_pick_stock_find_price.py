import numpy as np    
from sklearn import datasets, linear_model
from dateutil import relativedelta
import pandas as pd
from sqlalchemy import desc
import datetime as dt
import statsmodels.api as sm
from sklearn import preprocessing
import pickle
from six import StringIO


class stock_attribute_model():
    def __init__(self, code,params, initialStartIndex):
        self.params = params
        self.code = code
        self.startIndex = initialStartIndex        
        
# 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    # 定义一个全局变量, 保存要操作的股票
    # 000001(股票:平安银行)
    set_params()
    #设定沪深300作为基准
    set_benchmark('000300.XSHG')
    g.preprocess_data = True
    g.operating_revenue_growth_threshold = 2
    g.history_data_range = 600
    g.N = 5
    g.weight = 1/(float)(g.N)
    
    

def set_params():
    g.tc = 60 
    g.t = 0                # 记录回测运行的天数
    g.if_trade = False   
    g.initial_start_index = 651
    g.candidate_pool_set = False
    g.get_stocks = False
    # 设置调仓天数
        

def before_trading_start(context):
    # print 'get here '
    if not g.get_stocks:
        daily_operation(context)
        g.get_stocks = True
    
    

def daily_operation(context):
    candidates_stock = list(get_all_securities(['stock']).index)
    daily_mission_select_stock_obj = process_stocks(candidates_stock)
    context.wanted_stocks = daily_mission_select_stock_obj.get_proper_stocks(context)
    write_file('stockCandidates_linRegOnPrice', str(context.wanted_stocks), append=False)
    
    fetch_price_data_obj = fetch_price_data(context.wanted_stocks)
    
    historical_price = fetch_price_data_obj.get_train_data_model_stocks()
    
    write_file('linReg_price.csv', historical_price.to_csv(), append=False)
    print 'get here '



# class analyze_regression_model():
    

def set_slip_fee(context):
    # 将滑点设置为0
    set_slippage(PriceRelatedSlippage(0.002))
    # 根据不同的时间段设置手续费
    dt=context.current_dt
    log.info(type(context.current_dt))
    
    if dt>datetime.datetime(2013,1, 1):
        set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0013, min_cost=5)) 
        
    elif dt>datetime.datetime(2011,1, 1):
        set_commission(PerTrade(buy_cost=0.001, sell_cost=0.002, min_cost=5))
            
    elif dt>datetime.datetime(2009,1, 1):
        set_commission(PerTrade(buy_cost=0.002, sell_cost=0.003, min_cost=5))
                
    else:
        set_commission(PerTrade(buy_cost=0.003, sell_cost=0.004, min_cost=5))



        
# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    #update_position(context,data)
    pass
    
    
    # 获取股票的收盘价



        
class process_stocks():
    def __init__(self, stockList):
        self.stockList = stockList
        pass
    
    def get_proper_stocks(self, context, deltaday = 600):
        
        def remove_unwanted_stocks():
            current_data = get_current_data()
            return [stock for stock in self.stockList 
                if not current_data[stock].is_st  and (current_data[stock].name  is None or
                ( '*' not in current_data[stock].name 
                and '退' not in current_data[stock].name)) 
                and  not current_data[stock].paused]

        def fun_delNewShare(filtered_stocks):
            deltaDate = context.current_dt.date() - dt.timedelta(deltaday)
            tmpList = []
            for stock in filtered_stocks:
                if get_security_info(stock).start_date < deltaDate:
                    tmpList.append(stock)
            return tmpList
            
        def find_growing_stocks(filtered_stocks):
            query_str = query(indicator.code).filter(indicator.code.in_(filtered_stocks) ,\
                    valuation.pe_ratio < 400,  \
                    valuation.pe_ratio > 0, \
                    balance.total_owner_equities/balance.total_sheet_owner_equities > 0.2\
                    )
            df = get_fundamentals(query_str)
            promising_operating_growth_stocks = list(df['code'].values)
            return promising_operating_growth_stocks;
            
        unwanted_stocks = remove_unwanted_stocks()
        non_new_stocks = fun_delNewShare(unwanted_stocks)
        promising_stocks = find_growing_stocks(non_new_stocks)
        return promising_stocks
        
    #indicator.inc_operation_profit_annual > g.operating_revenue_growth_threshold

class fetch_price_data():
    def __init__(self, stockList):
        self.stockList = stockList
        
    def get_train_data_model_stocks(self):
        historical_data = history(g.history_data_range, unit='1d', field='close', security_list=self.stockList, df=True, \
                skip_paused=True, fq='pre')
        return historical_data
        
    
    
    
    
    
    
    
    
    
    
    
        
        
        
        
        