import numpy as np
import pickle
import random
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC

data_file = "data/preprocessed_data/data64.pkl"
data = []

with open(data_file,'rb') as f:
    data = pickle.load(f)

random.shuffle(data)

features = []
labels = []

for feature, label, in data:
    features.append(feature)
    labels.append(label)

xtrain,xtest,ytrain,ytest = train_test_split(features,labels,test_size=0.20)

model = SVC(C=1,gamma='auto',kernel='poly')
model.fit(xtrain,ytrain)

# with open('data/models/data64.sav','xb') as f:
#     pickle.dump(model,f)


prediction = model.predict(xtest)
accuracy = model.score(xtest,ytest)
print('Training Completed!')
print('Accuracy: ',accuracy)
print('Prediction is : ')