# Audio-data-pre-processing
-----
Audio pre-processing, especially, signal preprocessing related topics is not what I familiar with. My work and experience are mostly about CV and NLP and other data analysis areas.
But I am happy to learn new things, I used to learn FFT when I am a undergraduate student but never really use it. Redo the FFT part givea me some inspiration about how NN learns new features, you can find it on fft notebook. Mel-scale is completely new to me.

And I am not sure the connection between part 1 and 2, as I dont know how the 41 wav files and meta data can bu used further.

-----
### 0. data collection
- requests+beautifulsoup analyze soundwave website and extract necessory metadata including track_name,author,genre,play_count,download_count,comments_count,like_count,audio_url
- soundwave api for automatic audio downloading.
- ./data folder is too big, I will upload to Google drive and share later
### 1. audimetadata
- show meta data as request.
### 2. fft
- DFT: discrete Fourier Transform
- FFT: recurisive 1D FFT
- FFT_vectorized: non-recurisive vetorized FFT
- NN DFT: NN based DFT
- Different domain visualization
contains animation, if you cannot open on github please download or check the [colab version](https://colab.research.google.com/drive/14lrHSLRVrAMMyvkvXmMnZ8CJ4gfyL1p9?usp=sharing).
### 3. Spectrogram and mel-scale
- STFT
- Spectrogram with FFT and STFT
- Mel-scale filter bank
- Mel-scale Spectrogram
------
