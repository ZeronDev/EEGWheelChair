import os
import numpy as np
from pyriemann.estimation import Covariances
from pyriemann.tangentspace import TangentSpace
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from AiFilter import filterEEG
import joblib
from copy import deepcopy
from config import path

Chans = 4
Samples = 768
stride = 384

baseline_mean = None
clf = None
ts = None
scaler = None

try:
    model = joblib.load(path("models","pyriemann_model.pkl"))
    clf, ts, scaler = model["classifier"], model["tangent_space"], model["scaler"]
except Exception as e:
    pass

def augment_eeg(window, n_augment=3, noise_std=0.01, max_shift=10):
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

    eeg = ["left, right"]

    for class_id, file_name in enumerate(list(map(lambda x: x+".csv", eeg))):
        counter = 0
        eegFile = f"{os.path.splitext(file_name)[0]}{'' if not counter else counter}.csv"
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
            eegFile = f"{os.path.splitext(file_name)[0]}{counter}.csv"

    X = np.stack(X_list)
    y = np.array(y_list)
    return X, y

def train_pyriemann(X, y):
    global ts, scaler, clf
    cov = Covariances().fit_transform(X)
    ts = TangentSpace().fit(cov)
    X_ts = ts.transform(cov)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_ts)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, stratify=y)

    clf = LogisticRegression(max_iter=1000, multi_class='auto', solver='lbfgs')
    clf.fit(X_train, y_train)

    acc = clf.score(X_test, y_test)
    print(f"Test Accuracy: {acc*100:.2f}%")

    os.makedirs("models", exist_ok=True)
    joblib.dump({'classifier': clf, 'tangent_space': ts, 'scaler': scaler}, "models/pyRiemann_model.pkl")

def train():
    X, y = preprocess_data(n_augment=4)
    train_pyriemann(X, y)

if __name__ == "__main__":
    train()