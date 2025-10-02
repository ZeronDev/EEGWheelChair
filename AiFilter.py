from scipy.signal import butter, iirnotch, filtfilt

fs = 256  
lowcut = 0.5
highcut = 40.0
order = 4

# Bandpass (0.5 ~ 40Hz)
b_band, a_band = butter(order, [lowcut/(fs/2), highcut/(fs/2)], btype='band')

# Notch (60Hz)
f0 = 60.0 #한국의 경우 전력망이 60Hz
Q = 30.0
b_notch, a_notch = iirnotch(f0, Q, fs)

def filterEEG(data):
    y = filtfilt(b_band, a_band, data)
    y = filtfilt(b_notch, a_notch, y)
    return y
