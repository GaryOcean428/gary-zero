# Railway PyAudio Deployment Fix

## Issue Summary

Railway deployment failed when pip tried to install `pyaudio==0.2.14` during Docker build process with the error:

```text
src/pyaudio/device_api.c:9:10: fatal error: portaudio.h: 
No such file or directory
```

## Root Cause

PyAudio requires system-level PortAudio development headers and libraries for compilation.
These were missing from the Docker build environment.

## Solution

Added the following system dependencies to the Dockerfile:

### Builder Stage Dependencies

- `portaudio19-dev` - PortAudio development headers
- `libasound-dev` - ALSA development libraries  
- `libportaudio2` - PortAudio runtime library
- `libportaudiocpp0` - PortAudio C++ bindings
- `python3-dev` - Python development headers

### Runtime Stage Dependencies  

- `libportaudio2` - PortAudio runtime library
- `libportaudiocpp0` - PortAudio C++ bindings
- `libasound2` - ALSA runtime library

## Files Changed

- `Dockerfile` - Added system dependencies to both builder and runtime stages
- `test_pyaudio_import.py` - Created test to validate pyaudio functionality

## Validation

- PyAudio can be successfully installed and imported
- Audio device detection works gracefully in containerized environments
- No breaking changes to existing functionality
- Minimal impact (8 lines added to Dockerfile)

## Usage in Project

PyAudio is used for the Gemini Live API integration which provides:

- Bidirectional audio communication
- Audio device configuration
- Real-time voice interactions

## Notes for Developers

- PyAudio will show ALSA warnings in containerized environments without audio hardware - this is expected
- The audio functionality gracefully degrades when no audio devices are available
- System dependencies are essential for PyAudio compilation and must be installed before pip install

## Alternative Solutions Considered

1. Replace pyaudio with `sounddevice` (has pre-compiled wheels)
2. Make audio functionality optional
3. Use `pygame` for basic audio needs

The current solution was chosen to maintain compatibility with existing Gemini Live API integrations.
