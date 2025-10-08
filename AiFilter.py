from scipy.signal import butter, iirnotch, filtfilt, welch
import numpy as np


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


def check_qa(eegData): 
    eegData = np.array(eegData).T   # (samples, chans) → (chans, samples)

    voltage_thresh=100  # µV, spike 임계치
    delta_thresh=50     # 샘플 간 변화
    rms_thresh=10       # RMS 최소값
    contact_status = []

    for ch in range(4):
        signal = eegData[ch, :]   # 이제 OK

        # 1) Spike 감지
        spike_mask = (np.abs(signal) > voltage_thresh) | (np.abs(np.diff(signal, prepend=signal[0])) > delta_thresh)
        spike_flag = np.any(spike_mask)

        # 2) RMS 계산
        rms_value = np.sqrt(np.mean(signal**2))
        rms_flag = rms_value >= rms_thresh

        # 3) PSD 기반 체크 (Alpha 8-12Hz 파워)
        f, Pxx = welch(signal, fs=fs, nperseg=fs)
        alpha_power = np.sum(Pxx[(f >= 8) & (f <= 12)])
        psd_flag = alpha_power > 0.1  # 적절한 임계값은 실험 필요

        # 4) 최종 접촉 상태
        status = not spike_flag and rms_flag and psd_flag
        contact_status.append(status)

    return contact_status

def detect_blink(eeg_window):
    blink_thresh = 100  # µV 단위, 눈 깜빡임 spike 임계치
    blink_chs = [0, 1]
    for ch in blink_chs:
        sig = filtfilt(b_band, a_band, eeg_window[ch])
        if np.any(np.abs(sig) > blink_thresh):
            return True
    return False