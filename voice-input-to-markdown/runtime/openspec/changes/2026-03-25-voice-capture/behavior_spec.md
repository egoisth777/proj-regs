# Voice Capture Behavior Specification

## Scenario: Start voice capture session
Given the voice capture module is initialized with default settings
When the user starts a capture session
Then the microphone begins recording audio at 44100 Hz sample rate
And the audio buffer is written to a temporary WAV file

## Scenario: Stop voice capture and produce output
Given a voice capture session is active and recording
When the user stops the capture session
Then the recording stops and the audio file is finalized
And the audio data is passed to the markdown converter for transcription

## Scenario: Handle microphone not available
Given no microphone device is connected to the system
When the user attempts to start a capture session
Then an appropriate error message is returned indicating no audio input device was found
And the system does not crash or hang waiting for input
