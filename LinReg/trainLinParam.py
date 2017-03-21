import numpy as np
import pandas as pd
import pickle
import statsmodels.api as sm
from sklearn import preprocessing

#################################

preprocess_data = False
#data starts from 2016-03-01
count = 1


##################################
class stock_attribute_model():
    def __init__(self, code,params, rsquared, pvalues, initialStartIndex,variance):
        self.params = params
        self.code = code
        self.rsquared = rsquared
        self.pvalues = pvalues
        self.startIndex = initialStartIndex
        self.variance = variance

####################################################################


class linear_regression_model():
    def __init__(self):
        self.train_X = []
        self.train_Y = []
        #self.regr = linear_model.LinearRegression()
        
    def set_train_X_Y(self, train_X, train_Y):
        self.train_X = train_X
        self.train_Y = train_Y
        
    def data_cleaning(self):
    	print ('it is ', self.train_Y['002706.XSHE'][0])
    	return
    def scale_data(self, with_mean=True, with_std=False):
    	#self.data_cleaning()
        self.train_Y = preprocessing.scale(self.train_Y,with_mean=True, with_std=False)
        
    
    def fit_model(self,train_X,train_Y):
        self.set_train_X_Y(train_X, train_Y)
        if preprocess_data:
            self.scale_data()
        model = sm.OLS(self.train_Y, self.train_X)
        results = model.fit()
        # print(results.summary())
        return results.params, results.rsquared, results.pvalues

####################################################################

class model_selection():
	def __init__(self,model_List):
		self.model_list = model_List

	def calculte_oneThirdVarince(self):
		varianceList = []
		for model in self.model_list:
			varianceList.append(model.variance)
		varianceList.sort()
		self.one_third_variance = varianceList[int((float(1)/3)*len(varianceList))]
		return

	def calculte_oneThirdRsquare(self):
		rsquareList = []
		for model in self.model_list:
			rsquareList.append(model.rsquared)
		rsquareList.sort()
		self.one_third_rsquare = rsquareList[int((float(2)/3)*len(rsquareList))]
		return


	def calculate_mean_Rsquare(self):
		rsquareList = []
		for model in self.model_list:
			rsquareList.append(model.rsquared)
		self.mean_rsquare =  sum(rsquareList)/len(rsquareList)
		return

	def calculate_mean_slope(self):
		slopeList = []
		for model in self.model_list:
			slopeList.append(model.params[1])
		self.mean_slope =  sum(slopeList)/len(slopeList)
		return

	def filtered_model_list(self):
		self.calculate_mean_Rsquare()
		# self.calculate_mean_slope()
		self.calculte_oneThirdRsquare()
		self.calculte_oneThirdVarince()
		filtered_model_list = []
		for model in self.model_list:
			if model.params[1] >  0 \
				and model.rsquared > self.mean_rsquare:
				filtered_model_list.append(model)
		return filtered_model_list

	def filter_stocks(self):
		self.calculate_mean_Rsquare()
		self.calculate_mean_slope()
		filtered_model_list = []
		for model in self.model_list:
			if model.params[1] > self.mean_slope and model.rsquared> self.mean_rsquare:
				print ('the model pvalue is ', model.pvalues)
				filtered_model_list.append(model.code)
		return filtered_model_list

####################################################################
class model_factory():
	def __init__(self,stockList,data):
		self.stockList = stockList
		self.data = data
		pass

    
	def create_model_list(self):
		model_list = []
		for stock in self.stockList:
			linear_regression_model_obj = linear_regression_model()
			train_Y = self.data[stock].dropna()
			train_X = np.arange(1, len(train_Y) + 1)
			train_X = sm.add_constant(train_X)
			params, rsquare, pValues = linear_regression_model_obj.fit_model(train_X, train_Y.values)
			variance =  train_Y.var()
			initialStartIndex = len(train_X) + 1
			
			stock_attribute_model_obj = stock_attribute_model(stock, params, rsquare,pValues,initialStartIndex,variance)
			model_list.append(stock_attribute_model_obj)
		return model_list


####################################################################

class save_model():
    def __init__(self, model_list):
        self.model_list = model_list
        pass
    def write_file(self,code_file,params_file,startIndexFile):
        codeList = []
        for model in self.model_list:
            codeList.append(model.code)
        print ('A length is ', len(codeList))
        write_file(code_file, str(codeList), append=False)
        paramList = []
        for model in self.model_list:
            paramList.append(model.params)
        print ('B length is ', len(paramList))
        write_file(params_file, str(paramList), append=False)
        startIndexList = []
        for model in self.model_list:
            startIndexList.append(model.startIndex)
            print ('C length is ', len(startIndexList))
        write_file(startIndexFile, str(startIndexList), append=False)

####################################################################
data = pd.read_csv('linReg_price.csv', low_memory=False)

data.drop(data.columns[0], axis = 1, inplace=True)
stock_list = list(data.columns)
first_column = data.iloc[:,:1]

model_factory_obj = model_factory(stock_list,data)
model_list = model_factory_obj.create_model_list()
model_selection_obj = model_selection(model_list)
model_selected_list = model_selection_obj.filtered_model_list()
save_model_obj = save_model(model_selected_list)
save_model_obj.write_file('linReg_data_code', 'linReg_data_params', 'linReg_data_StartIndex')


