from scipy.signal import butter, iirnotch, filtfilt, welch
import numpy as np


fs = 256  
lowcut = 8.0
highcut = 30.0
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

def check_qa(eegData):
    threshold = 150.0
    eegData = np.std(np.array(eegData), axis=0)  # (samples, chans)
    contact_status = eegData <= threshold

    return contact_status



def detect_blink(eeg_window):
    blink_thresh = 200  # µV 단위, 눈 깜빡임 spike 임계치
    blink_chs = [0, 1]
    for ch in blink_chs:
        sig = filtfilt(b_band, a_band, eeg_window[ch])
        if np.any(np.abs(sig) > blink_thresh):
            return True
    return False