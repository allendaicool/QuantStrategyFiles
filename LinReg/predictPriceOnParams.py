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
    # 设置调仓天数
        

def before_trading_start(context):
    if not g.candidate_pool_set:
        read_stocks_linReg_obj = read_stocks_linReg()
        read_stocks_linReg_obj.read_from_pickle_file('linReg_data.pkl',context)
    
    if g.t%g.tc==0:
        #每g.tc天，交易一次
        g.if_trade=True 
        # 设置手续费与手续费
        set_slip_fee(context) 
        select_stocks(context)
        
    g.t+=1

# def daily_operation(context):
#     candidates_stock = list(get_all_securities(['stock']).index)
#     daily_mission_select_stock_obj = process_stocks(candidates_stock)
#     context.wanted_stocks = daily_mission_select_stock_obj.get_proper_stocks(context)
#     write_file('stockCandidates_linRegOnPrice', str(context.wanted_stocks), append=False)
    
#     fetch_price_data_obj = fetch_price_data(context.wanted_stocks)
    
#     historical_price = fetch_price_data_obj.get_train_data_model_stocks()
    
#     write_file('linReg_price.csv', historical_price.to_csv(), append=False)




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



def select_stocks(context):
    select_top_five_stocks_obj = select_top_five_stocks()
    context.selected_stocks = select_top_five_stocks_obj.analyze_trend(context)

def update_position(context, data):
    def sell_stock():
        for p in context.portfolio.positions:
            if p not in context.selected_stocks :
                o = order_target(p, 0)
            
    def buy_stock():
        target_value = g.weight * context.portfolio.portfolio_value
        for s in context.selected_stocks:
            o = order_target_value(s, target_value)
        
    sell_stock()
    buy_stock()
        
# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    update_position(context,data)
    pass
    
    
    # 获取股票的收盘价


class read_stocks_linReg():
    def __init__(self):
        pass
    
    def read_from_pickle_file(self,fileName,context):
        g.candidate_pool_set = True
        rd_code = read_file('linReg_data_code')
        rd_code = eval(rd_code)
        rd_params = read_file('linReg_data_params')
        rd_params = eval(rd_params)

        rd_startIndex = read_file('linReg_data_StartIndex')
        rd_startIndex = eval(rd_startIndex)

        print ('type is ', type(rd_params))
        print ('rd code len is ', len(rd_code))
        print ('rd_params len is ', len(rd_params))
        print ('rd_startIndex len is ', len(rd_startIndex))


        context.model_list = []
        for i in range(len(rd_code)):
            stock_attribute_model_obj = stock_attribute_model(rd_code[i], rd_params[i],rd_startIndex[i] )
            context.model_list.append(stock_attribute_model_obj)
        
        print ('type is ', type(rd_params))
        
        context.candidates_pool = []
        for model in context.model_list:
            context.candidates_pool.append(model.code)
        return

class select_top_five_stocks():
    def __init__(self):
        pass
    
    def get_unsuspended_stocks(self,context):
        current_data = get_current_data()
        return  [stock for stock in context.candidates_pool if not  current_data[stock].paused]
    
    def get_yesterday_close_price(self,stockList):
        price_df = history(1, unit='1d', field='close', \
            security_list=stockList, df=True, skip_paused=False, fq='pre')
        price_df.index = ['price']
        return price_df
    
    def scan_pool_predicted_price(self,stockList,context):
        stock_dict= {}
        for model in context.model_list:
            if model.code in stockList:
                predicted_price = model.startIndex * model.params[1] + model.params[0]
                stock_dict[model.code] = [predicted_price]
                model.params[1] += 1
        
        predicted_price_df = pd.DataFrame.from_items(stock_dict.items(), orient='columns')
        predicted_price_df.index = ['price']
        return predicted_price_df
        
    def analyze_trend(self,context):
        unsuspendedStocks = self.get_unsuspended_stocks(context)
        actual_last_day_priced_df = self.get_yesterday_close_price(unsuspendedStocks)
        predicted_price_df = self.scan_pool_predicted_price(unsuspendedStocks,context)
        
        ratio = actual_last_day_priced_df.iloc[0,:]/predicted_price_df.iloc[0,:]
        ratio.sort()
        return list(ratio[:5].index)
        
        
        
            
  
        
        
# class process_stocks():
#     def __init__(self, stockList):
#         self.stockList = stockList
#         pass
    
#     def get_proper_stocks(self, context, deltaday = 600):
        
#         def remove_unwanted_stocks():
#             current_data = get_current_data()
#             return [stock for stock in self.stockList 
#                 if not current_data[stock].is_st  and (current_data[stock].name  is None or
#                 ( '*' not in current_data[stock].name 
#                 and '退' not in current_data[stock].name)) 
#                 and  not current_data[stock].paused]

#         def fun_delNewShare(filtered_stocks):
#             deltaDate = context.current_dt.date() - dt.timedelta(deltaday)
#             tmpList = []
#             for stock in filtered_stocks:
#                 if get_security_info(stock).start_date < deltaDate:
#                     tmpList.append(stock)
#             return tmpList
            
                    
                
#         def find_growing_stocks(filtered_stocks):
#             query_str = query(indicator.code).filter(indicator.code.in_(filtered_stocks) ,\
#                     valuation.pe_ratio < 400,  \
#                     valuation.pe_ratio > 0, \
#                     balance.total_owner_equities/balance.total_sheet_owner_equities > 0.6,\
#                     indicator.inc_operation_profit_annual > g.operating_revenue_growth_threshold)
#             df = get_fundamentals(query_str)
#             promising_operating_growth_stocks = list(df['code'].values)
#             return promising_operating_growth_stocks;
            
#         unwanted_stocks = remove_unwanted_stocks()
#         non_new_stocks = fun_delNewShare(unwanted_stocks)
#         promising_stocks = find_growing_stocks(non_new_stocks)
#         return promising_stocks
        
    

# class fetch_price_data():
#     def __init__(self, stockList):
#         self.stockList = stockList
        
#     def get_train_data_model_stocks(self):
#         historical_data = history(g.history_data_range, unit='1d', field='close', security_list=self.stockList, df=True, \
#                 skip_paused=True, fq='pre')
#         return historical_data
        
    
    
    
    
    
    
    
    
    
    
    
        
        
        
        
        