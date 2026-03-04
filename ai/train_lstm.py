import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.utils import to_categorical
from dataset import load_dna_sequences

# Load data
sequences, next_chars = load_dna_sequences("dna_data.txt")

mapping = {'A': 0, 'T': 1, 'G': 2, 'C': 3}
reverse_mapping = {v: k for k, v in mapping.items()}

X = []
y = []

for seq, next_char in zip(sequences, next_chars):
    X.append([mapping[c] for c in seq])
    y.append(mapping[next_char])

X = np.array(X)
y = np.array(y)

X = to_categorical(X, num_classes=4)
y = to_categorical(y, num_classes=4)

# Build LSTM model
model = Sequential()
model.add(LSTM(64, input_shape=(X.shape[1], 4)))
model.add(Dense(4, activation='softmax'))

model.compile(
    loss='categorical_crossentropy',
    optimizer='adam'
)

model.fit(X, y, epochs=50, batch_size=64)

model.save("dna_lstm_model.h5")
print("DNA LSTM model trained and saved")
