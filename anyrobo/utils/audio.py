"""Audio processing utilities for AnyRobo."""

import numpy as np
from typing import Tuple, Optional


class AudioProcessor:
    """Utilities for processing audio data."""
    
    @staticmethod
    def detect_silence(
        audio: np.ndarray, 
        threshold: float = 0.02, 
        min_duration: int = 10
    ) -> np.ndarray:
        """Detect silent regions in audio data.
        
        Args:
            audio: Audio data as numpy array
            threshold: Volume level that counts as silence
            min_duration: Minimum number of consecutive frames to consider as silence
            
        Returns:
            Boolean array where True indicates silence
        """
        # Calculate the amplitude envelope
        amplitude = np.abs(audio)
        
        # Detect silence based on threshold
        is_silent = amplitude < threshold
        
        # Apply minimum duration (simplistic approach)
        for i in range(len(is_silent) - min_duration):
            if np.all(is_silent[i:i+min_duration]):
                is_silent[i:i+min_duration] = True
                
        return is_silent
    
    @staticmethod
    def trim_silence(
        audio: np.ndarray, 
        threshold: float = 0.02, 
        min_silence_duration: int = 1000
    ) -> np.ndarray:
        """Trim silence from the beginning and end of audio data.
        
        Args:
            audio: Audio data as numpy array
            threshold: Volume level that counts as silence
            min_silence_duration: Minimum silence duration in samples
            
        Returns:
            Trimmed audio data
        """
        # Find the first non-silent sample
        amplitude = np.abs(audio)
        is_silent = amplitude < threshold
        
        # Find start (first non-silent frame)
        start = 0
        while start < len(audio) and is_silent[start]:
            start += 1
            
        # Find end (last non-silent frame)
        end = len(audio) - 1
        while end > 0 and is_silent[end]:
            end -= 1
            
        return audio[start:end+1]
    
    @staticmethod
    def resample(
        audio: np.ndarray, 
        orig_sample_rate: int, 
        target_sample_rate: int
    ) -> np.ndarray:
        """Resample audio to a different sample rate.
        
        Args:
            audio: Audio data as numpy array
            orig_sample_rate: Original sample rate of the audio
            target_sample_rate: Target sample rate
            
        Returns:
            Resampled audio data
        """
        if orig_sample_rate == target_sample_rate:
            return audio
            
        # Simple resampling using linear interpolation
        # For production, use a proper resampling library like scipy.signal or librosa
        duration = len(audio) / orig_sample_rate
        new_length = int(duration * target_sample_rate)
        indices = np.linspace(0, len(audio) - 1, new_length)
        indices = indices.astype(np.int32)
        return audio[indices] 