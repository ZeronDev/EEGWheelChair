import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models # type: ignore
from tensorflow.keras.constraints import max_norm # type: ignore
from tensorflow.keras.callbacks import Callback # type: ignore
import config
from config import path
import os
import DataManager
from AiFilter import filterEEG

tf.config.run_functions_eagerly(True)

def build_eegnet(nb_classes, Chans, Samples, dropoutRate=0.3):
    input1 = layers.Input(shape=(Chans, Samples, 1))

    # Block 1
    x = layers.Conv2D(8, (1, 64), padding='same', use_bias=False)(input1)
    x = layers.BatchNormalization()(x)
    x = layers.DepthwiseConv2D((Chans, 1), use_bias=False, depth_multiplier=2,depthwise_constraint=max_norm(1.))(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('elu')(x)
    x = layers.AveragePooling2D((1, 4))(x)
    x = layers.Dropout(dropoutRate)(x)

    # Block 2
    x = layers.SeparableConv2D(16, (1, 16), use_bias=False, padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('elu')(x)
    x = layers.AveragePooling2D((1, 8))(x)
    x = layers.Dropout(dropoutRate)(x)

    # Classifier
    x = layers.Flatten()(x)
    x = layers.Dense(nb_classes, kernel_constraint=max_norm(0.25))(x)
    out = layers.Activation('softmax')(x)

    return models.Model(inputs=input1, outputs=out)

model = None

if os.path.exists(path("models", "EEGNet.h5")):
    model = models.load_model(path("models", "EEGNet.h5"))
else:
    nb_classes = 4
    model = build_eegnet(nb_classes, Chans=4, Samples=256)
    model.compile(loss='sparse_categorical_crossentropy', optimizer=tf.keras.optimizers.Adam(), metrics=['accuracy'], run_eagerly=True)

Chans = 4
Samples = 256
stride = 128
batch_size = 16

def train():
    global model
    
    X_list, y_list = [], []

    for class_id, file_name in enumerate(list(map(lambda x: x+".csv", DataManager.eegData))):
        data = np.loadtxt(path("data", file_name), delimiter=',')

        filtered_data = np.zeros_like(data)
        for ch in range(data.shape[1]):  # 각 채널 반복
            filtered_data[:, ch] = filterEEG(data[:, ch])
            
        for start in range(0, data.shape[0] - Samples + 1, stride):
            window = filtered_data[start:start+Samples].T[..., np.newaxis]  # (Chans, Samples, 1)
            X_list.append(window)
            y_list.append(class_id)
    X_train = np.stack(X_list)  # (총 trial 수, Chans, Samples, 1)
    y_train = np.array(y_list)  # (총 trial 수,
    model.fit(X_train, y_train, batch_size=16, epochs=50, shuffle=True, callbacks=[CTkProgressBarCallback()])
    model.save(path("models", "EEGNet.h5"))

class CTkProgressBarCallback(Callback):
    def __init__(self):
        super().__init__()
        self.progressbar = config.app.progress
        self.progressbar.grid(row=2, column=0, padx=20, pady=10, sticky="nsew", columnspan=2)

    def on_epoch_begin(self, epoch, logs=None):
        self.current_epoch = epoch
        self.epochs = self.params['epochs']
        self.steps_per_epoch = self.params['steps']

    def on_batch_end(self, batch, logs=None):
        total_batches = self.epochs * self.steps_per_epoch
        current_batch = self.current_epoch * self.steps_per_epoch + batch + 1
        progress_value = current_batch / total_batches
        self.progressbar.set(progress_value)
        self.progressbar.master.update()  # UI 갱신