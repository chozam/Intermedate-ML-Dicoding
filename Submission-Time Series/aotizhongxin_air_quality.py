# -*- coding: utf-8 -*-
"""Aotizhongxin-Air-Quality.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1mpKc0YCZVsYXBI8uIvq9r_0azWjLAx35

# **Aotizhongxin-Air-Quality**

Data from: https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data
"""

import pandas as pd
import numpy as np
from keras.layers import LSTM, Dense
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from keras.callbacks import Callback, EarlyStopping

df = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/dataset/PRSA_Data_Aotizhongxin_20130301-20170228.csv')

print(len(df))

df.head()

df['date'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
df.drop(df.iloc[:, 0:8], inplace=True, axis=1)
df

df.drop(df.iloc[:, 1:10], inplace=True, axis=1)
df

df.isna().sum()

mean_no2 = df['NO2'].mean()
df['NO2'].fillna(mean_no2, inplace=True)

df = df.dropna(how='any',axis=0)
df.isna().sum()

date = df['date'].values
no2 = df['NO2'].values

plt.figure(figsize=(15,5))
plt.plot(date, no2)
plt.title('NO2 Average', fontsize=20);

temp_train, temp_test = train_test_split(no2, test_size=0.2, shuffle=False)
min_max_scaler = MinMaxScaler()
min_max_scaler.fit(np.array(temp_train).reshape(-1, 1))
train = min_max_scaler.transform(np.array(temp_train).reshape(-1, 1))
test = min_max_scaler.transform(np.array(temp_test).reshape(-1, 1))

print(train)

def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
  series = tf.expand_dims(series, axis=-1)
  ds = tf.data.Dataset.from_tensor_slices(series)
  ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
  ds = ds.flat_map(lambda w: w.batch(window_size + 1))
  ds = ds.shuffle(shuffle_buffer)
  ds = ds.map(lambda w: (w[:-1], w[-1:]))
  return ds.batch(batch_size).prefetch(1)

threshold_mae = (np.max(train) - np.min(train)) * 10/100
print(threshold_mae)

window_size = 60
train_set = windowed_dataset(train, window_size=window_size, batch_size=128, shuffle_buffer=1000)
test_set = windowed_dataset(test, window_size=window_size, batch_size=128, shuffle_buffer=1000)
model = tf.keras.models.Sequential([
    tf.keras.layers.Conv1D(filters=32,
                          kernel_size=5,
                          strides=1,
                          padding='causal',
                          activation='relu',
                          input_shape=[window_size, 1]),
    tf.keras.layers.LSTM(64, input_shape=(window_size, 1), return_sequences=True),
    tf.keras.layers.LSTM(64),
    tf.keras.layers.Dropout(0.4),
    tf.keras.layers.Dense(30, activation='relu'),
    tf.keras.layers.Dense(10, activation='relu'),
    tf.keras.layers.Dense(1),
])

class MyCallback(Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('mae')<threshold_mae):
      self.model.stop_training = True
callback = MyCallback()
early_stopping = EarlyStopping(monitor='val_mae', patience=15)

optimizer = tf.keras.optimizers.SGD(learning_rate=1.0000e-04, momentum=0.9)
model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=['mae'])
history_train = model.fit(train_set,
                          validation_data=(test_set),
                          epochs= 100,
                          verbose=2,
                          callbacks = [callback, early_stopping])

plt.plot(history_train.history['loss'])
plt.plot(history_train.history['val_loss'])
plt.title('Loss Model')
plt.ylabel('Accuracy')
plt.xlabel('epoch')
plt.legend(['Train','Test'], loc='upper right')
plt.show()

plt.plot(history_train.history['mae'])
plt.plot(history_train.history['val_mae'])
plt.title('MAE Model')
plt.ylabel('MAE')
plt.xlabel('epoch')
plt.legend(['Train','Test'], loc='upper right')
plt.show()