import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Input, Conv2D, DepthwiseConv2D, SeparableConv2D
from tensorflow.keras.layers import BatchNormalization, Activation, AveragePooling2D, Dropout, Flatten, Dense
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from AiFilter import filterEEG  # 기존 필터

Chans = 4
Samples = 768
stride = 384

baseline_data = np.loadtxt(os.path.join("data", "base.csv"), delimiter=',')
baseline_mean = np.mean(baseline_data, axis=0, keepdims=True)

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
    # EEGNet 입력: (samples, channels, time, 1)
    X = X[..., np.newaxis]
    y = to_categorical(y)
    return X, y

# -----------------------------
# EEGNet 모델 정의
# -----------------------------
def create_eegnet(nb_classes=2, Chans=4, Samples=768, dropoutRate=0.1, kernLength=64, F1=8, D=2, F2=16):
    input1 = Input(shape=(Chans, Samples, 1))

    # Block 1
    block1 = Conv2D(F1, (1, kernLength), padding='same', use_bias=False)(input1)
    block1 = BatchNormalization()(block1)
    block1 = DepthwiseConv2D((Chans, 1), depth_multiplier=D, use_bias=False, depthwise_constraint=tf.keras.constraints.max_norm(1.))(block1)
    block1 = BatchNormalization()(block1)
    block1 = Activation('elu')(block1)
    block1 = AveragePooling2D((1, 4))(block1)
    block1 = Dropout(dropoutRate)(block1)

    # Block 2
    block2 = SeparableConv2D(F2, (1, 16), padding='same', use_bias=False)(block1)
    block2 = BatchNormalization()(block2)
    block2 = Activation('elu')(block2)
    block2 = AveragePooling2D((1, 8))(block2)
    block2 = Dropout(dropoutRate)(block2)

    flatten = Flatten()(block2)
    dense = Dense(nb_classes, activation='softmax')(flatten)

    model = Model(inputs=input1, outputs=dense)
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model

# -----------------------------
# 학습
# -----------------------------
if __name__ == "__main__":
    X, y = preprocess_data(n_augment=3)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, stratify=y, random_state=42)

    model = create_eegnet()
    model.summary()

    model.fit(X_train, y_train, batch_size=16, epochs=50, validation_data=(X_test, y_test))

    # 모델 저장
    model.save("models/eegnet_model.h5")
model = load_model("models/eegnet_model.h5")