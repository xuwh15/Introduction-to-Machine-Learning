import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso, RidgeCV
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import mean_squared_error, roc_auc_score
import math
import csv
from xgboost import XGBRegressor
from sklearn.feature_selection import SelectKBest, f_classif, chi2, f_regression,SelectFromModel
from sklearn.svm import SVR, SVC
from scipy import stats
from statistics import mean 

VITALS = ['LABEL_RRate', 'LABEL_ABPm', 'LABEL_SpO2', 'LABEL_Heartrate']
TESTS = ['LABEL_BaseExcess', 'LABEL_Fibrinogen', 'LABEL_AST', 'LABEL_Alkalinephos', 'LABEL_Bilirubin_total',
         'LABEL_Lactate', 'LABEL_TroponinI', 'LABEL_SaO2',
         'LABEL_Bilirubin_direct', 'LABEL_EtCO2']
         
def data_process(train_path, test_path, label_path):
	train = load_data(train_path)
	test = load_data(test_path)
	label = load_data(label_path)
	
	train = feature_augment(train);
	print('training data size after feature augmentation:'); print(train.shape)
	test = feature_augment(test);
	print('testing data size after feature augmentation:'); print(test.shape)
	
	train = train.fillna(0);
	test = test.fillna(0);
	# if we should do normalization? if we set the nan to zero.
	
	return train, test, label
	
	
def load_data(data_path):
	data = pd.read_csv(data_path)
	#X_train = train.drop(['Id','y'],axis=1)
	#y_train = train.y
	#X_test = test.drop(['Id'],axis=1)
	return data

def feature_augment(data):
	mean_data = data.groupby('pid').mean();
	max_data = data.groupby('pid').max();
	min_data = data.groupby('pid').min();
	median_data = data.groupby('pid').median();
	data = pd.concat([mean_data,max_data,min_data, median_data],axis=1)
	return data
	
def feature_transform(data):
	n,m = data.shape
	new_data = np.zeros(n*21).reshape(n,21)
	new_data[:,0:5] = data[:,0:5]
	new_data[:,5:10] = np.power(data[:,0:5],2); #element wise multiplication
	print(new_data[1,5:10])
	print(data[1,0:5])
	new_data[:,10:15] = np.exp(data[:,0:5])
	new_data[:,15:20] = np.cos(data[:,0:5])
	new_data[:,20] = 1
	# order: 1,11,10
	#new_data = np.delete(new_data,idx,1)
	return new_data
	
def feature_selection(data,y,num_feature):
	select = SelectKBest(f_regression, k=num_feature).fit(data,y)
	#select = SelectFromModel(estimator=Lasso(), threshold=-np.inf, max_features=num_feature).fit(data,y)
	new_data = select.transform(data);
	idx = select.get_support()
	#print(idx)
	#new_data = np.delete(new_data,idx,1)
	return new_data
	
def feature_selection_by_corre(data,y):
	for i in range(21):
		print(stats.pearsonr(data[:,i],y))
	return data
	
def ridgecv(X,y):
	reg = RidgeCV(alphas=[1e-1,1,10,100], fit_intercept=False, cv=30).fit(X,y)
	return reg

def ridge(X,y,alpha):
	reg = Ridge(alpha=alpha,fit_intercept='False',tol=1e-6,solver='svd');
	reg.fit(X,y)
	return reg

def svc(X,y):
	clf = SVC(probability=True, class_weight='balanced');
	clf.fit(X,y);
	return clf;

def xgb(X,y):
	xg_reg = XGBRegressor(objective ='binary:logistic', colsample_bytree = 0.3, learning_rate = 0.3,
	max_depth = 5, alpha = 10, n_estimators = 100);
	xg_reg.fit(X,y);
	return xg_reg;
                
def cross_validation(data, Y_train, kfold):
	score = 0
	score_train = 0
	kfold = 5
	kf = KFold(n_splits = kfold)
	alpha = 10
	weight = 0
	m,n = data.shape
	for train_index, val_index in kf.split(data):
		x_train, x_val= data[train_index], data[val_index]
		y_train, y_val = Y_train[train_index], Y_train[val_index]
		#reg = svc(x_train, y_train)
		reg = xgb(x_train,y_train)
		#y_val_pred = reg.predict_proba(x_val) # shape: (n_sample, n_class)
		y_val_pred = reg.predict(x_val)
		#score += roc_auc_score(y_val, y_val_pred[:,1]) * len(y_val)
		score += roc_auc_score(y_val, y_val_pred) * len(y_val)
		#score_train += (mean_squared_error(reg.predict(x_train), y_train)) * len(y_train)
		#weight += reg.coef_
	return (score / len(Y_train))

def print_to_csv(weight,idx):
	j = 0;
	weight_ = np.zeros(21);
	for i in range(21):
		#if i in idx:
		if idx[i] == False:
			weight_[i] = 0
		else:
			weight_[i] = weight[j]
			j += 1
	result = pd.DataFrame(weight_)
	result.to_csv('./weight.csv',indata_processdex=False,header=False)
	
def do_task1(train, label_data, test):
	total_score = [];
	print("using 10 % of data");
	for label in TESTS:
		print(label)
		x_data = train.sort_values('pid').values;
		x_label = label_data.sort_values('pid')[label].values;
		
		# do feature selection before training
		x_data = feature_selection(x_data,x_label,70);
		score = cross_validation(x_data, x_label, 20);
		total_score.append(score);
		print("score of {}:{}".format(label, score));
	print("average score of subtask1:{}".format(mean(total_score)));
	return
		

def main():
	train_path = './train_features.csv';
	test_path = './test_features.csv';
	label_path = './train_labels.csv';
	train, test, label = data_process(train_path, test_path, label_path); # still return pandaFrame

	do_task1(train, label, test)
	# if need values, just use 'train.values' it will return numpy array, label['LABEL_ABPm'].values to return labels.
	
    # task 2
    # task 3
    
	#kfold = 20
	#loss = np.inf
	#weight_ = np.zeros(21)
	#for num_feature in range(10,15):
#		data_, idx = feature_selection(data, Y_train,num_feature)
#		weight , val_loss = cross_validation(data_, Y_train, kfold)
#		if val_loss<loss: 
#			loss = val_loss; 
#			weight_ = weight; 
#			best_num = num_feature;
#			idx_ = idx;
		
	#data, idx = feature_selection(data, Y_train,num_feature)
main()
		
		
