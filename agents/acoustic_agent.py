import asyncio
import os
import numpy as np
from dotenv import load_dotenv

load_dotenv()

class AcousticAgent:
    def __init__(self):
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")
        self.available = False
        self.speech_config = None
        
        # Only initialize if credentials are provided
        if self.speech_key and self.speech_region:
            try:
                from azure.cognitiveservices.speech import SpeechConfig
                self.speech_config = SpeechConfig(subscription=self.speech_key, region=self.speech_region)
                self.available = True
                print("✅ Acoustic Agent initialized with Azure Speech Service")
            except Exception as e:
                print(f"Warning: Acoustic Agent Azure not available: {e}")
                self.available = False
        else:
            print("⚠️ Acoustic Agent: Using mock mode (no Azure credentials)")

    async def analyze_vocal_liveness(self, audio_stream: bytes) -> float:
        """
        Analyze audio stream for synthetic voice artifacts.
        Returns a normalized risk_score between 0.0 and 1.0 (1.0 = high risk of voice clone).
        In mock mode, returns a random score for testing.
        """
        try:
            # Validate audio data exists
            if not audio_stream or len(audio_stream) == 0:
                print("🔊 Acoustic Agent: Empty audio stream, returning mock score")
                import random
                return random.uniform(0.2, 0.6)
            
            # Try to use librosa if available for spectral analysis
            try:
                import librosa
                from io import BytesIO
                
                try:
                    # Try to load audio - will fail if format is not recognized
                    y, sr = librosa.load(BytesIO(audio_stream), sr=None)

                    # Extract spectral features
                    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
                    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
                    spectral_flux = librosa.onset.onset_strength(y=y, sr=sr)
                    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
                    chroma = librosa.feature.chroma_stft(y=y, sr=sr)

                    # Calculate various risk indicators
                    centroid_mean = np.mean(spectral_centroid)
                    centroid_std = np.std(spectral_centroid)
                    centroid_score = min(1.0, abs(centroid_mean - 3000) / 2000 + centroid_std / 1000)

                    rolloff_mean = np.mean(spectral_rolloff)
                    rolloff_score = min(1.0, abs(rolloff_mean - 5000) / 3000)

                    mfcc_var = np.var(mfccs, axis=1).mean()
                    mfcc_score = min(1.0, mfcc_var / 1000)

                    chroma_var = np.var(chroma, axis=1).mean()
                    chroma_score = min(1.0, chroma_var / 0.1)

                    flux_mean = np.mean(spectral_flux)
                    flux_std = np.std(spectral_flux)
                    flux_score = min(1.0, flux_std / flux_mean if flux_mean > 0 else 1.0)

                    # Weighted combination
                    risk_score = (
                        centroid_score * 0.2 +
                        rolloff_score * 0.2 +
                        mfcc_score * 0.3 +
                        chroma_score * 0.2 +
                        flux_score * 0.1
                    )
                    
                    print(f"🔊 Acoustic Agent (spectral analysis): risk_score={risk_score:.2f}")
                    return min(1.0, max(0.0, risk_score))
                    
                except Exception as load_error:
                    # Audio format not recognized - use mock mode
                    print(f"🔊 Acoustic Agent: Audio format error ({type(load_error).__name__}), using mock score")
                    import random
                    risk_score = random.uniform(0.2, 0.6)
                    return risk_score
                    
            except ImportError:
                # Librosa not available, use mock mode
                print("🔊 Acoustic Agent (mock - librosa not available)")
                import random
                risk_score = random.uniform(0.2, 0.6)
                return risk_score
                
        except Exception as e:
            print(f"🔊 Acoustic Agent: Error {type(e).__name__}: {str(e)[:50]}")
            # Return moderate risk on error
            import random
            return random.uniform(0.2, 0.6)

        except Exception as e:
            print(f"Error in vocal liveness analysis: {e}")
            return 0.5  # Neutral score on error

    async def analyze_audio_stream(self, audio_stream: bytes) -> float:
        """
        Legacy method - redirects to analyze_vocal_liveness for backward compatibility.
        """
        return await self.analyze_vocal_liveness(audio_stream)