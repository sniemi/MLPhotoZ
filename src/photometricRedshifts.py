"""
Photometric Redshifts
=====================

This scripts shows simple methods to derive photometric redshifts using machine learning.

Data can be downloaded from the Kaggle website:
https://inclass.kaggle.com/c/PhotometricRedshiftEstimation/data

:requires: pandas
:requires: numpy
:requires: scikit-learn
:requires: matplotlib

tested with:
pandas 0.15.2
Numpy 1.9.1
sklearn 0.15.2
matplotlib 1.4.2

:author: Sami-Matias Niemi
:contact: s.niemi@icloud.com
:version: 0.8
"""
import matplotlib
matplotlib.rcParams['font.size'] = 17
matplotlib.rc('xtick', labelsize=14)
matplotlib.rc('axes', linewidth=1.1)
matplotlib.rcParams['legend.fontsize'] = 11
matplotlib.rcParams['legend.handlelength'] = 3
matplotlib.rcParams['xtick.major.size'] = 5
matplotlib.rcParams['ytick.major.size'] = 5
matplotlib.rcParams['image.interpolation'] = 'none'
import matplotlib as mpl
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn import cross_validation
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor as GBR
from sklearn import linear_model
from sklearn.svm import SVR
from sklearn import grid_search
from sklearn.cross_validation import cross_val_score
from sklearn.learning_curve import validation_curve
from sklearn.learning_curve import learning_curve
from sklearn import metrics
from sklearn import preprocessing
import copy
import cPickle


def loadKaggledata(folder='MachineLearning/photo-z/kaggleData/', useErrors=True):
    """
    Load Kaggle photometric redshift competition data. These data are from 2012 and at low-z.

    train: ID, u, g, r, i, z, uErr, gErr, rErr, iErr, zErr, redshift
    query: ID, u, g, r, i, z, uErr, gErr, rErr, iErr, zErr
    solution: ID, redshift, estimatedRedshiftError
    """
    filename = folder + 'train.csv'
    data = pd.read_csv(filename, index_col=0, usecols=['ID', 'u', 'g', 'r', 'i', 'z',
                                                       'modelmagerr_u', 'modelmagerr_g',
                                                       'modelmagerr_r', 'modelmagerr_i',
                                                       'modelmagerr_z', 'redshift'])
    if useErrors:
        data_features = data[['u', 'g', 'r', 'i', 'z',
                              'modelmagerr_u', 'modelmagerr_g',
                              'modelmagerr_r', 'modelmagerr_i',
                              'modelmagerr_z']]
    else:
        data_features = data[['u', 'g', 'r', 'i', 'z']]
    data_redshifts = data[['redshift']]

    X_train, X_test, y_train, y_test = train_test_split(data_features.values,
                                                        data_redshifts.values,
                                                        test_size=0.35,
                                                        random_state=42)
    # remove mean dn scale to unit variance
    scaler = preprocessing.StandardScaler().fit(X_train)    
    X_train = scaler.transform(X_train)                                                    
    X_test = scaler.transform(X_test)                                                    

    #make 1D vectors
    y_train = y_train.ravel()
    y_test = y_test.ravel()

    print "feature vector shape=", data_features.values.shape
    print 'Training sample shape=', X_train.shape
    print 'Testing sample shape=', X_test.shape
    print 'Target training redshift sample shape=', y_train.shape
    print 'Testing redshift sample shape=',  y_test.shape

    return X_train, X_test, y_train, y_test



def plot_learning_curve(estimator, title, X, y, ylim=None, cv=None,
                        n_jobs=1, train_sizes=np.linspace(.1, 1.0, 5)):
    """
    Generate a simple plot of the test and training learning curve.

    Parameters
    ----------
    estimator : object type that implements the "fit" and "predict" methods
        An object of that type which is cloned for each validation.

    title : string
        Title for the chart.

    X : array-like, shape (n_samples, n_features)
        Training vector, where n_samples is the number of samples and
        n_features is the number of features.

    y : array-like, shape (n_samples) or (n_samples, n_features), optional
        Target relative to X for classification or regression;
        None for unsupervised learning.

    ylim : tuple, shape (ymin, ymax), optional
        Defines minimum and maximum yvalues plotted.

    cv : integer, cross-validation generator, optional
        If an integer is passed, it is the number of folds (defaults to 3).
        Specific cross-validation objects can be passed, see
        sklearn.cross_validation module for the list of possible objects

    n_jobs : integer, optional
        Number of jobs to run in parallel (default 1).
    """
    plt.figure()
    plt.title(title)
    if ylim is not None:
        plt.ylim(*ylim)
    plt.xlabel("Training examples")
    plt.ylabel("Score")
    train_sizes, train_scores, test_scores = learning_curve(
        estimator, X, y, cv=cv, n_jobs=n_jobs, train_sizes=train_sizes)
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)

    plt.fill_between(train_sizes, train_scores_mean - train_scores_std,
                     train_scores_mean + train_scores_std, alpha=0.1,
                     color="r")
    plt.fill_between(train_sizes, test_scores_mean - test_scores_std,
                     test_scores_mean + test_scores_std, alpha=0.1, color="g")
    plt.plot(train_sizes, train_scores_mean, 'o-', color="r",
             label="Training score")
    plt.plot(train_sizes, test_scores_mean, 'o-', color="g",
             label="Cross-validation score")

    plt.legend(loc="best", shadow=True, fancybox=True)
    return plt
    

def randomForest(X_train, X_test, y_train, y_test, search=True, save=False):
    """
    A random forest regressor.

    A random forest is a meta estimator that fits a number of classifying decision
    trees on various sub-samples of the dataset and use averaging to improve the
    predictive accuracy and control over-fitting.

    Can run a grid search to look for the best parameters (search=True) and
    save the model to a file (save=True).
    """
    if search:
        # parameter values over which we will search
        parameters = {'min_samples_split': [1, 2, 3, 10],
                      'min_samples_leaf': [1, 2, 3, 10],
                     'max_features': [None, 'sqrt', 7],
                     'max_depth': [None, 15, 30, 40]}
        rf = RandomForestRegressor(n_estimators=100, n_jobs=4, verbose=1)
        #note: one can run out of memory if using n_jobs=-1..
        rf_tuned = grid_search.GridSearchCV(rf, parameters, scoring='r2', n_jobs=2, verbose=1, cv=3)
    else:
        rf_tuned = RandomForestRegressor(n_estimators=2000,
                                         max_depth=28,
                                         max_features=7,
                                         min_samples_split=2,
                                         min_samples_leaf=2,
                                         n_jobs=-1, verbose=1)
       #n_estimators=5000 will take about 36GB of RAM

    print '\nTraining...'
    rf_optimised = rf_tuned.fit(X_train, y=y_train)
    print 'Done'
    
    if search:
        print 'The best score and estimator:'
        print(rf_optimised.best_score_)
        print(rf_optimised.best_estimator_)
        rf_optimised = rf_optimised.best_estimator_

    if save:
        print 'Save the Random Forest to a pickled file; note that the model can quickly take 100G'
        fp = open('model/RF.pkl', 'w')
        cPickle.dump(rf_optimised, fp)
        fp.close()

    print '\nPredicting...'
    predicted = rf_optimised.predict(X_test)
    expected = y_test.copy()
    print 'Done'

    return predicted, expected
    
    
def SupportVectorRegression(X_train, X_test, y_train, y_test, search, save=False):
    """
    Support Vector Regression.
    
    Can run a grid search to look for the best parameters (search=True) and
    save the model to a file (save=True).    
    """
    if search:
        # parameter values over which we will search
        parameters = {'C': [0.1, 0.5, 1., 1.5, 2.],
                     'kernel': ['rbf', 'sigmoid', 'poly'],
                     'degree': [3, 5]}
        s = SVR()
        clf = grid_search.GridSearchCV(s, parameters, scoring='r2',
                                       n_jobs=-1, verbose=1, cv=3)
    else:
        clf = SVR(verbose=1)
    
    print '\nTraining...'
    clf.fit(X_train, y_train)
    print 'Done'

    if search:
        print 'The best score and estimator:'
        print(clf.best_score_)
        print(clf.best_estimator_)
        print 'Best hyperparameters:'
        print clf.best_params_
        clf = clf.best_estimator

    if save:
        print 'Save the SVR model to a pickled file...'
        fp = open('model/SVR.pkl', 'w')
        cPickle.dump(clf, fp)
        fp.close()

    print '\nPredicting...'
    predicted = clf.predict(X_test)
    expected = y_test.copy()    
    print 'Done'

    return predicted, expected    
 
    
def BayesianRidge(X_train, X_test, y_train, y_test, search=True):
    """
    Bayesian Ridge Regression.
    """
    print '\nTraining...'
    clf = linear_model.BayesianRidge(n_iter=1000, tol=1e-3, alpha_1=1., 
                                     fit_intercept=True, normalize=False, verbose=1)
    clf.fit(X_train, y_train)
    print 'Done'
    
    print '\nPredicting...'
    predicted = clf.predict(X_test)
    expected = y_test.copy()    
    print 'Done'

    return predicted, expected    


def GradientBoostingRegressor(X_train, X_test, y_train, y_test, search, save=False):
    """
    GB builds an additive model in a forward stage-wise fashion;
    it allows for the optimization of arbitrary differentiable loss functions.
    In each stage a regression tree is fit on the negative gradient of the
    given loss function.

    Can run a grid search to look for the best parameters (search=True) and
    save the model to a file (save=True).    
    Among the most important hyperparameters for GBRT are:

        #. number of regression trees (n_estimators)
        #. depth of each individual tree (max_depth)
        #. loss function (loss)
        #. learning rate (learning_rate)

    """   
    if search:
        # parameter values over which we will search
        parameters = {'loss': ['ls', 'huber'],
                     'learning_rate': [0.001, 0.01, 0.05, 0.1, 0.5],
                     'max_depth': [1, 2, 3, 5, 7, None],
                     'max_features': ['sqrt', None]}
        s = GBR(n_estimators=500, verbose=1)
        clf = grid_search.GridSearchCV(s, parameters, scoring='r2',
                                       n_jobs=-1, verbose=1, cv=3)
    else:
        clf = GBR(verbose=1, n_estimators=5000,learning_rate=0.05, loss='huber', max_depth=3, subsample=0.8)
        
    print '\nTraining...'    
    clf.fit(X_train, y_train)
    print 'Done'

    if search:
        print 'The best score and estimator:'
        print(clf.best_score_)
        print(clf.best_estimator_)
        print 'Best hyperparameters:'
        print clf.best_params_
        clf = clf.best_estimator_

    if save:
        print 'Save the BGR model to a pickled file...'
        fp = open('model/GBR.pkl', 'w')
        cPickle.dump(clf, fp)
        fp.close()
 
    print '\nPredicting...'
    predicted = clf.predict(X_test)
    expected = y_test.copy()    
    print 'Done'

    return predicted, expected    


def randomForestTestPlots(X_train, X_test, y_train, y_test):
    """
    Validation Curve
    ================
    Underfitting - both the training and the validation score are low. 
    Overfitting - training score is good but the validation score is low.
    When the score is high for both, the method is working pretty well.
    
    Learning Curve
    ==============
    learning curve shows the validation and training score of an estimator
    for varying numbers of training samples. It is a tool to find out how much
    we benefit from adding more training data and whether the estimator
    suffers more from a variance error or a bias error. If both the validation
    score and the training score converge to a value that is too low with
    increasing size of the training set, we will not benefit much from more
    training data.
    """
    title = "Validation Curve (Random Forest)"
    print title
    param_range = np.round(np.linspace(0, 60, 15) + 1).astype(np.int)
    rf = RandomForestRegressor(n_estimators=100,
                               max_features=6,
                               min_samples_split=2,
                               n_jobs=2, verbose=1)
    #validation curve
    train_scores, test_scores = validation_curve(rf,
                                                 X_train,
                                                 y_train,
                                                 'max_depth',
                                                 param_range,
                                                 n_jobs=-1,
                                                 verbose=1)
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)

    plt.title(title)
    plt.xlabel("max_depth")
    plt.ylabel("Score")
    plt.ylim(0.8, 1.01)
    plt.plot(param_range, train_scores_mean, label="Training score", color="r")
    plt.fill_between(param_range, train_scores_mean - train_scores_std,
                     train_scores_mean + train_scores_std, alpha=0.2, color="r")
    plt.plot(param_range, test_scores_mean, label="Cross-validation score",
                 color="g")
    plt.fill_between(param_range, test_scores_mean - test_scores_std,
             test_scores_mean + test_scores_std, alpha=0.2, color="g")
    plt.legend(loc="best")
    plt.savefig('RandomForestValidationCurve.pdf')
    plt.close()

    #learning curve
    title = "Learning Curves (Random Forest)"
    print title
    cv = cross_validation.ShuffleSplit(X_train.shape[0], n_iter=50,
                                       test_size=0.2, random_state=0)
    
    plot_learning_curve(rf, title, X_train, y_train, ylim=(0.85, 1.01), cv=cv, n_jobs=-1)
    plt.savefig('RandomForestLearningCurve.pdf')
    plt.close()



def GradientBoostingRegressorTestPlots(X_train, X_test, y_train, y_test, n_estimators=1000):
    """
    An important diagnostic when using GBRT in practise is the so-called deviance
    plot that shows the training/testing error (or deviance) as a function of the
    number of trees.
    """
    def fmt_params(params):
        return ", ".join("{0}={1}".format(key, val) for key, val in params.iteritems())
        
    def deviance_plot(est, X_test, y_test, ax=None, label='', train_color='#2c7bb6', 
                      test_color='#d7191c', alpha=1.0):
        """Deviance plot for ``est``, use ``X_test`` and ``y_test`` for test error. """
        test_dev = np.empty(n_estimators)
    
        for i, pred in enumerate(est.staged_predict(X_test)):
           test_dev[i] = est.loss_(y_test, pred)
    
        if ax is None:
            fig = plt.figure(figsize=(8, 5))
            ax = plt.gca()
            
        ax.plot(np.arange(n_estimators) + 1, test_dev, color=test_color, label='Test %s' % label, 
                 linewidth=2, alpha=alpha)
        ax.plot(np.arange(n_estimators) + 1, est.train_score_, color=train_color, 
                 label='Train %s' % label, linewidth=2, alpha=alpha)
        ax.set_ylabel('Error')
        ax.set_xlabel('n_estimators')
        return test_dev, ax

    est = GBR(n_estimators=n_estimators, verbose=1)
    est.fit(X_train, y_train)
    feature_importance = est.feature_importances_
    
    test_dev, ax = deviance_plot(est, X_test, y_test)
    ax.legend(loc='upper right')
    ax.annotate('Lowest test error', xy=(test_dev.argmin() + 1, test_dev.min() + 0.02), xycoords='data',
                xytext=(150, 1.0), textcoords='data',
                arrowprops=dict(arrowstyle="->", connectionstyle="arc"))
    plt.savefig('GBRdeviance.pdf')
    plt.close()
        
    #sample leaves
    fig = plt.figure(figsize=(8, 5))
    ax = plt.gca()
    for params, (test_color, train_color) in [({'min_samples_leaf': 1},
                                                ('#d7191c', '#2c7bb6')),
                                              ({'min_samples_leaf': 4},
                                               ('#fdae61', '#abd9e9'))]:
        est = GBR(n_estimators=n_estimators, verbose=1)
        est.set_params(**params)
        est.fit(X_train, y_train)
        
        test_dev, ax = deviance_plot(est, X_test, y_test, ax=ax, label=fmt_params(params),
                                     train_color=train_color, test_color=test_color)
    plt.legend(loc='upper right')
    plt.savefig('GBRTree.pdf')
    plt.close()
    
    #lerning rate
    fig = plt.figure(figsize=(8, 5))
    ax = plt.gca()
    for params, (test_color, train_color) in [({'learning_rate': 0.2},
                                                ('#d7191c', '#2c7bb6')),
                                              ({'learning_rate': 0.7},
                                               ('#fdae61', '#abd9e9'))]:
        est = GBR(n_estimators=n_estimators, verbose=1)
        est.set_params(**params)
        est.fit(X_train, y_train)
        
        test_dev, ax = deviance_plot(est, X_test, y_test, ax=ax, label=fmt_params(params),
                                     train_color=train_color, test_color=test_color)
    plt.legend(loc='upper right')
    plt.savefig('GBRShrinkage.pdf')
    plt.close()
    
    #sub-samples
    fig = plt.figure(figsize=(8, 5))
    ax = plt.gca()
    for params, (test_color, train_color) in [({'subsample': 1.},
                                                ('#d7191c', '#2c7bb6')),
                                              ({'subsample': 0.7},
                                               ('#fdae61', '#abd9e9'))]:
        est = GBR(n_estimators=n_estimators, verbose=1)
        est.set_params(**params)
        est.fit(X_train, y_train)
        
        test_dev, ax = deviance_plot(est, X_test, y_test, ax=ax, label=fmt_params(params),
                                     train_color=train_color, test_color=test_color)
    plt.legend(loc='upper right')
    plt.savefig('GBRSubsample.pdf')
    plt.close()    
    
    #feature importance
    feature_names = ['u', 'g', 'r', 'i', 'z', 'modelmagerr_u', 'modelmagerr_g',
                     'modelmagerr_r', 'modelmagerr_i', 'modelmagerr_z']
    feature_names = np.asarray(feature_names)
    feature_importance = 100.0 * (feature_importance / feature_importance.max())
    sorted_idx = np.argsort(feature_importance)
    pos = np.arange(sorted_idx.shape[0]) + .5
    plt.subplot(1, 1, 1)
    plt.barh(pos, feature_importance[sorted_idx], align='center')
    plt.yticks(pos, feature_names[sorted_idx])
    plt.xlabel('Relative Importance')
    plt.title('Variable Importance')
    plt.savefig('GBRImportance.pdf')
    plt.close()


def plotResults(predicted, expected, output):
    """
    Generate a simple plot demonstrating the results.
    """
    var = metrics.explained_variance_score(expected, predicted)
    mae = metrics.mean_absolute_error(expected, predicted)
    mse = metrics.mean_squared_error(expected, predicted)
    r2 = metrics.r2_score(expected, predicted)
    rms = np.sqrt(np.mean((expected - predicted) ** 2))

    print output
    print 'Explained variance (best possible score is 1.0, lower values are worse):', var
    print 'Mean Absolute Error (best is 0.0):', mae
    print 'Mean Squred Error (best is 0.0):', mse
    print 'R2 score (best is 1.0):', r2
    print 'RMS:', rms
    print '\n\n\n'

    title = 'RMS=%.4f, MSE=%.4f, R2=%.3f' % (rms, mse, r2)

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    plt.title(title)
    ax1.scatter(expected, predicted, alpha=0.2, s=5)
    ax1.set_xlabel("Spectroscopic Redshift")
    ax1.set_ylabel("Photo-z")
    ax1.plot([0, 8], [0, 8], '-r')
    ax1.set_xlim(0, 1.1*expected.max())
    ax1.set_ylim(0, 1.1*expected.max())
    plt.savefig(output+'Results.pdf')
    plt.close()



def runRandomForestKaggle(useErrors=True, search=False, test=False):
    """
    Simple Random Forest on Kaggle training data.
    """
    X_train, X_test, y_train, y_test = loadKaggledata(useErrors=useErrors)
    if test: randomForestTestPlots(X_train, X_test, y_train, y_test)
    predictedRF, expectedRF = randomForest(X_train, X_test, y_train, y_test, search=search)
    plotResults(predictedRF, expectedRF, output='RandomForestKaggleErrors')


def runBayesianRidgeKaggle(useErrors=True):
    """
    Run Bayesian Ridge on Kaggle training data.
    """
    X_train, X_test, y_train, y_test = loadKaggledata(useErrors=useErrors)
    predicted, expected = BayesianRidge(X_train, X_test, y_train, y_test)
    plotResults(predicted, expected, output='BayesianRidgeKaggleErrors')
    
    
def runSupportVectorRegression(useErrors=False, search=False):
    """
    Pretty slow to run.
    """
    X_train, X_test, y_train, y_test = loadKaggledata(useErrors=useErrors)
    predicted, expected = SupportVectorRegression(X_train, X_test, y_train, y_test, search)
    plotResults(predicted, expected, output='SVRKaggleErrors')    


def runGradientBoostingRegressor(useErrors=True, search=False, test=True):
    """
    Run Gradient Boosting on Kaggle training data.
    """
    X_train, X_test, y_train, y_test = loadKaggledata(useErrors=useErrors)
    if test: GradientBoostingRegressorTestPlots(X_train, X_test, y_train, y_test)
    predicted, expected = GradientBoostingRegressor(X_train, X_test, y_train, y_test, search)
    plotResults(predicted, expected, output='GBRKaggleErrors')    

    
if __name__ == '__main__':
    runGradientBoostingRegressor()
    runBayesianRidgeKaggle()
    runRandomForestKaggle()
