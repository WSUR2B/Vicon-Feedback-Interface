import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import firwin, lfilter

FilterTypes = ['none', 'bandpass', 'moving_average', 'moving_median', 'kalman']

class MyFilter:
    """
    A class that implements various types of filters for signal processing.

    Attributes:
        window_size (int): The size of the filter window.
        samplingRate (float): The sampling rate of the input signal.
        filter_type (str): The type of filter to be applied.
        lowcut (float): The lower cutoff frequency for the bandpass filter (default: 50.0).
        highcut (float): The upper cutoff frequency for the bandpass filter (default: 300.0).
        filter_buffer (numpy.ndarray): The buffer used for storing previous data points.
        delay (float): The delay introduced by the filter.

    Methods:
        __init__(self, window_size, samplingRate, filter_type, lowcut=50.0, highcut=300.0):
            Initializes the MyFilter object with the specified parameters.

        create_bandpass_filter(self, lowcut, highcut, fs, numtaps):
            Creates a bandpass filter with the specified cutoff frequencies.

        kalman_filter(self, measurement):
            Applies the Kalman filter to the given measurement.

        filter(self, data):
            Applies the selected filter to the input data.

    """

    def __init__(self, window_size, samplingRate, filter_type, lowcut=50.0, highcut=300.0):
        """
        Initializes the MyFilter object with the specified parameters.

        Args:
            window_size (int): The size of the filter window.
            samplingRate (float): The sampling rate of the input signal.
            filter_type (str): The type of filter to be applied.
            lowcut (float, optional): The lower cutoff frequency for the bandpass filter (default: 50.0).
            highcut (float, optional): The upper cutoff frequency for the bandpass filter (default: 300.0).
        """
        self.window_size = window_size
        self.filter_type = filter_type
        self.filter_buffer = np.zeros(window_size)
        self.delay = (window_size-1)/2/samplingRate

        self.impulse_response = []
        if filter_type == 'bandpass':
            self.impulse_response = self.create_bandpass_filter(lowcut, highcut, samplingRate, window_size)
        elif filter_type == 'moving_average':
            self.impulse_response = np.ones(window_size)/window_size
        elif filter_type == 'moving_median':
            self.impulse_response = []
        elif filter_type == 'kalman':
            # Initialize Kalman filter parameters
            self.state_estimate = np.array([[0], [0]])  # Initial state estimate
            self.estimate_covariance = np.eye(2)  # Initial estimate covariance
            self.state_transition_model = np.array([[1, 0], [0, 1]])  # State transition model
            self.observation_model = np.array([[1, 0]])  # Observation model
            self.process_noise_covariance = np.array([[1, 0], [0, 1]]) * 0.001  # Process noise covariance
            self.measurement_noise_covariance = np.array([[1]]) * 0.001  # Measurement noise covariance
            self.control_input_model = None  # Control input model (not used in this example)
            self.control_input = None  # Control input (not used in this example)

    def create_bandpass_filter(self, lowcut, highcut, fs, numtaps):
        """
        Creates a bandpass filter with the specified cutoff frequencies.

        Args:
            lowcut (float): The lower cutoff frequency.
            highcut (float): The upper cutoff frequency.
            fs (float): The sampling rate of the input signal.
            numtaps (int): The number of taps (filter coefficients) to be used.

        Returns:
            numpy.ndarray: The impulse response of the bandpass filter.
        """
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        return firwin(numtaps, [low, high], pass_zero=False)
    
    def kalman_filter(self, measurement):
        """
        Applies the Kalman filter to the given measurement.

        Args:
            measurement (float): The measurement to be filtered.

        Returns:
            float: The filtered value.
        """
        # Prediction step
        predicted_state_estimate = np.dot(self.state_transition_model, self.state_estimate)
        predicted_estimate_covariance = np.dot(self.state_transition_model, np.dot(self.estimate_covariance, self.state_transition_model.T)) + self.process_noise_covariance

        # Observation update
        innovation = measurement - np.dot(self.observation_model, predicted_state_estimate)
        innovation_covariance = np.dot(self.observation_model, np.dot(predicted_estimate_covariance, self.observation_model.T)) + self.measurement_noise_covariance
        kalman_gain = np.dot(predicted_estimate_covariance, np.dot(self.observation_model.T, np.linalg.inv(innovation_covariance)))

        # Update estimates
        self.state_estimate = predicted_state_estimate + np.dot(kalman_gain, innovation)
        identity_matrix = np.eye(self.estimate_covariance.shape[0])
        self.estimate_covariance = np.dot((identity_matrix - np.dot(kalman_gain, self.observation_model)), predicted_estimate_covariance)

        # Assuming the first element of the state estimate is the filtered value 
        filtered_value = self.state_estimate[0, 0]
        return filtered_value
    
    def filter(self, data):
        """
        Applies the selected filter to the input data.

        Args:
            data (numpy.ndarray): The input data to be filtered.

        Returns:
            numpy.ndarray: The filtered data.
        """
        if self.filter_type == 'none':
            return data
        elif self.filter_type == 'moving_median':
            # Update the buffer with the new data point
            self.filter_buffer = np.roll(self.filter_buffer, -1)
            self.filter_buffer[-1] = data
            return np.median(self.filter_buffer)
        elif self.filter_type == 'kalman':
            return self.kalman_filter(data)
        else:
            # Update the buffer with the new data point
            self.filter_buffer = np.roll(self.filter_buffer, -1)
            self.filter_buffer[-1] = data
            return np.dot(self.filter_buffer, self.impulse_response)