import scipy
import numpy
from sklearn import linear_model
from sklearn.metrics import roc_auc_score,roc_curve,auc
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.cross_validation import StratifiedKFold
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pylab
from scipy import interp

def load_movie_info():
    f = open('movie_info.csv', 'r')
    lines = f.readlines()
    f.close()

    movie_info = []
    for line in lines:
        line = line.strip()
        movie_info.append(line.split(','))
    
    movie_info = format_fields(movie_info)
    
    return movie_info 


def load_movie_info_before_release():
    f = open('movie_info.csv', 'r')
    lines = f.readlines()
    f.close()

    movie_info = []
    for line in lines:
        line = line.strip()
        movie_info.append(line.split(','))

    movie_info = format_fields(movie_info)
    for row in movie_info:
        del row[5]

    return movie_info


def format_fields(movie_info):
    for i in range(0, len(movie_info)):

	#extract mpaa rating from text value
    	mpaa = movie_info[i][3]
        mpaa_rating = mpaa.split(' ')
	if len(mpaa_rating) == 0:
                movie_info[i][3] = 0
	elif mpaa_rating[0] =="Rated" and len(mpaa_rating)>0:
		movie_info[i][3] = mpaa_rating[1]
	elif "R" in mpaa_rating:
        	movie_info[i][3] = "R"
	elif "PG" in mpaa_rating:
                movie_info[i][3] = "PG"
	elif "PG-13" in mpaa_rating:
                movie_info[i][3] = "PG-13"
	else:
		movie_info[i][3] = 0
	
	#remove $ sign from budget
	budget = movie_info[i][4]
	if len(budget) == 0:
		movie_info[i][4] = 0
	elif budget[0] == '$': 
		movie_info[i][4] = budget[1:]
	else:
		movie_info[i][4] = 0

	#extract opening_weekend amount value
	opening_weekend =  movie_info[i][5]
	opening_weekend_arr = opening_weekend.split(' ')
	if len(opening_weekend_arr) > 0 and len(opening_weekend_arr[0]) > 0 and opening_weekend_arr[0][0] == '$':
                open_wknd = opening_weekend_arr[0]
                movie_info[i][5] = open_wknd[1:]
	else:
		movie_info[i][5] = 0

	#extract gross amount value
        gross =  movie_info[i][15]
        gross_arr = gross.split(' ')
        if len(gross_arr) > 0 and len(gross_arr[0]) > 0 and gross_arr[0][0] == '$':
                gross = gross_arr[0]
                movie_info[i][15] = gross[1:]
        else:
                movie_info[i][15] = 0
        
    return movie_info


def create_input(movie_info):
    # don't want to cinlude movie_id, title, country in predicition
    SKIP = 3
    WIDTH = len(movie_info[0]) - SKIP
    X = scipy.zeros((len(movie_info), WIDTH))
    for i in range(0, len(movie_info)):
        for j in range(SKIP, WIDTH):
		try:
	                X[i, j-SKIP] = movie_info[i][j] if movie_info[i][j] != '' else 0
		except Exception:
			pass
    return X


def create_output(movie_info):
    Y = scipy.zeros(len(movie_info))
    for i in range(0, len(movie_info)):
        gross = movie_info[i][15]
        if gross > 1000000:
            Y[i] = 1
    print 'Number of successful movies', sum(Y)
    return Y

def create_output_before_release(movie_info):
    Y = scipy.zeros(len(movie_info))
    for i in range(0, len(movie_info)):
        gross = movie_info[i][14]
        if gross > 1000000:
            Y[i] = 1
    print 'Number of successful movies', sum(Y)
    return Y


def test_classifier(clf, X, Y, loc):
    folds = StratifiedKFold(Y, 5)
    mean_tpr = 0.0
    mean_fpr = numpy.linspace(0, 1, 100)
    aucs = []

    for i, (train, test) in enumerate(folds):
        clf.fit(X[train], Y[train])
        prediction = clf.predict_proba(X[test])
        aucs.append(roc_auc_score(Y[test], prediction[:, 1]))
        
	false_positive_rate, true_positive_rate, thresholds = roc_curve(Y[test], prediction[:, 1])
        mean_tpr += interp(mean_fpr, false_positive_rate, true_positive_rate)
        mean_tpr[0] = 0.0
	roc_auc = auc(false_positive_rate, true_positive_rate)
	plt.plot(false_positive_rate, true_positive_rate, lw=1,
	label='ROC fold %d (area = %0.2f)' % ( i, roc_auc))
    plt.plot([0, 1], [0, 1], '--', color=(0.6, 0.6, 0.6), label='Luck')
    mean_tpr /= len(folds)
    mean_tpr[-1] = 1.0
    mean_auc = auc(mean_fpr, mean_tpr)
    plt.plot(mean_fpr, mean_tpr, 'k--',
         label='Mean ROC (area = %0.2f)' % mean_auc, lw=2)

    plt.title('Receiver Operating Characteristic')
    plt.xlim([0,1])
    plt.ylim([0,1])
    plt.ylabel('True Positive Rate')
    plt.xlabel('False Positive Rate')
    plt.legend(loc='lower right')
    plt.show()
    plt.savefig('plots/'+loc+'/'+clf.__class__.__name__+'.png')
    plt.clf()
    print clf.__class__.__name__, aucs, numpy.mean(aucs)

	
def main():
    #before_release
    movie_info_before_release = load_movie_info_before_release()
    print '***Before release***'
    
    X = create_input(movie_info_before_release)
    Y = create_output_before_release(movie_info_before_release)

    clf = linear_model.SGDClassifier(loss='log')
    test_classifier(clf, X, Y, 'before_release')

    clf = GaussianNB()
    test_classifier(clf, X, Y, 'before_release')

    clf = RandomForestClassifier(n_estimators=10, max_depth=10)
    test_classifier(clf, X, Y, 'before_release')
   
    #After release
    movie_info = load_movie_info()
    print '***After release***'	
    
    X = create_input(movie_info)
    Y = create_output(movie_info)

    clf = linear_model.SGDClassifier(loss='log')
    test_classifier(clf, X, Y, 'after_release')

    clf = GaussianNB()
    test_classifier(clf, X, Y, 'after_release')

    clf = RandomForestClassifier(n_estimators=10, max_depth=10)
    test_classifier(clf, X, Y, 'after_release')


if __name__ == '__main__':
    main()

