# Voice Capture Test Specification

## Unit Tests

### test_voice_capture_init
Verify that VoiceCapture initializes with correct default sample rate of 44100 Hz and mono channel configuration. Assert that the internal audio buffer is empty on creation.

### test_voice_capture_start_recording
Verify that calling start_recording sets the is_recording flag to True and opens the audio stream. Mock the microphone device to avoid hardware dependency.

### test_voice_capture_stop_recording
Verify that calling stop_recording after a session finalizes the audio buffer, closes the stream, and returns the path to the output file.

### test_audio_utils_noise_reduction
Verify that the noise reduction utility reduces background noise amplitude by at least 50% while preserving speech frequency ranges between 300 Hz and 3400 Hz.

### test_markdown_converter_basic
Verify that the markdown converter takes raw transcribed text and produces valid markdown with appropriate heading levels and paragraph breaks.
