import os
import numpy as np
from pyriemann.estimation import Covariances
from pyriemann.tangentspace import TangentSpace
# from pyriemann.classification import MDM, SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from AiFilter import filterEEG
import joblib

from config import path
from sklearn.svm import SVC 

Chans = 4
Samples = 768
stride = int(Samples / 2)

baseline_data = np.loadtxt(os.path.join("data", "base.csv"), delimiter=',')
baseline_mean = np.mean(baseline_data, axis=0, keepdims=True)
pipeline = None

try:
    pipeline = joblib.load(path("models","pyRiemann_model.pkl"))
    
except Exception as e:
    print(e)

def augment_eeg(window, n_augment=3, noise_std=0.02, max_shift=10):
    augmented = []
    for _ in range(n_augment):
        w = window.copy()
        w += np.random.normal(0, noise_std, w.shape)
        shift = np.random.randint(-max_shift, max_shift+1)
        if shift > 0:
            w = np.concatenate([np.zeros((w.shape[0], shift)), w[:, :-shift]], axis=1)
        elif shift < 0:
            w = np.concatenate([w[:, -shift:], np.zeros((w.shape[0], -shift))], axis=1)
        augmented.append(w)
    return augmented

def preprocess_data(n_augment=3):
    global baseline_mean
    X_list, y_list = [], []

    baseline_data = np.loadtxt(os.path.join("data", "base.csv"), delimiter=',')
    baseline_mean = np.mean(baseline_data, axis=0, keepdims=True)

    eeg = ["left","right"]

    for class_id, class_name in enumerate(eeg):
        counter = 0
        eegFile = f"{class_name}{'' if not counter else counter}.csv"

        while os.path.exists(os.path.join("data", eegFile)) or counter == 0:
            data = np.loadtxt(os.path.join("data", eegFile), delimiter=',')
            filtered_data = np.zeros_like(data)
            for ch in range(data.shape[1]):
                filtered_data[:, ch] = filterEEG(data[:, ch])
            
            # sliding window
            for start in range(0, data.shape[0]-Samples+1, stride):
                window = filtered_data[start:start+Samples].T
                window -= baseline_mean.T
                window = (window - window.mean(axis=1, keepdims=True)) / (window.std(axis=1, keepdims=True) + 1e-6)

                X_list.append(window)
                y_list.append(class_id)

                # 증강
                augmented = augment_eeg(window, n_augment=n_augment)
                X_list.extend(augmented)
                y_list.extend([class_id]*len(augmented))

            counter += 1
            eegFile = f"{class_name}{counter}.csv"

    X = np.stack(X_list)
    y = np.array(y_list)
    return X, y

def train_pyriemann(X, y):
    global pipeline
    pipeline = Pipeline([
        ('cov', Covariances(estimator='lwf')), # 공분산 행렬 추정
        ('ts', TangentSpace()),                # 리만 공간 -> 유클리드 접선 공간으로 변환
        ('scaler', StandardScaler()),          # 유클리드 특징 벡터 스케일링 (평균 0, 분산 1)
        ('clf', CalibratedClassifierCV(SVC(kernel='rbf', C=1.0), method='sigmoid',cv=3))   # 선형 SVM 분류기
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, stratify=y)
    pipeline.fit(X_train, y_train)
    # clf = SVC(kernel='linear', C=1.0)#LogisticRegression(max_iter=1000, multi_class='auto', solver='lbfgs')
    # clf.fit(X_train, y_train)

    test_acc = pipeline.score(X_test, y_test)
    train_acc = pipeline.score(X_train, y_train)
    print(f"Test Accuracy: {test_acc*100:.2f}%\nTrain Accuracy: {train_acc*100:.2f}%")

    # cv = KFold(n_splits=5, shuffle=True, random_state=42)
    # scores = cross_val_score(pipeline, X, y, cv=cv, scoring='accuracy', n_jobs=-1)
    # print(scores)

    os.makedirs("models", exist_ok=True)
    joblib.dump(pipeline, "models/pyRiemann_model.pkl")

def train():
    X, y = preprocess_data(n_augment=3)
    train_pyriemann(X, y)

if __name__ == "__main__":
    train()