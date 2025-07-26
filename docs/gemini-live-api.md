# Google Gemini Live API Integration

This document provides comprehensive guidance for using the Google Gemini Live API integration in Gary-Zero.

## Overview

The Gemini Live API integration enables real-time voice and video streaming with Google's advanced AI models. This feature provides:

- **Low-latency bidirectional audio streaming**
- **Multiple voice options** (Zephyr, Echo, Crystal, Sage)
- **Configurable response modalities** (Audio now, Video coming soon)
- **WebSocket-based real-time communication**
- **Seamless integration with Gary-Zero's agent framework**

## Setup Instructions

### 1. Environment Configuration

Add the following environment variables to your `.env` file:

```bash
# Required: Gemini API Key
GEMINI_API_KEY=your-gemini-api-key-here

# Optional: Default Configuration
GEMINI_LIVE_MODEL=models/gemini-2.5-flash-preview-native-audio-dialog
GEMINI_LIVE_VOICE=Zephyr
GEMINI_LIVE_RESPONSE_MODALITIES=AUDIO
```

### 2. Get Your API Key

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a new API key or use an existing one
3. Copy the API key to your environment variables

### 3. Install Dependencies

The integration requires WebSocket support (already included in requirements):

```bash
pip install websockets
```

Note: Audio functionality requires `pyaudio` but will gracefully degrade if not available.

## Usage

### Web UI Configuration

1. **Open Settings**: Click the settings icon in the Gary-Zero web interface
2. **Navigate to Gemini Live**: Find the "Gemini Live API" section
3. **Configure Settings**:
   - Enter your API key
   - Select model (default: gemini-2.5-flash-preview-native-audio-dialog)
   - Choose voice (Zephyr, Echo, Crystal, Sage)
   - Configure response modalities (Audio, Video when available)
4. **Test Connection**: Use the "Test Connection" button to verify your setup
5. **Start Streaming**: Click "Start Streaming" to begin real-time interaction

### Tool Usage

You can also use the Gemini Live API through Gary-Zero's tool system:

#### Start Streaming Session

```json
{
  "action": "start_streaming",
  "api_key": "your-api-key",
  "model": "models/gemini-2.5-flash-preview-native-audio-dialog",
  "voice": "Zephyr",
  "response_modalities": ["AUDIO"]
}
```

#### Stop Streaming Session

```json
{
  "action": "stop_streaming"
}
```

#### Check Status

```json
{
  "action": "status"
}
```

#### Configure Parameters

```json
{
  "action": "configure",
  "voice": "Echo",
  "response_modalities": ["AUDIO"]
}
```

### API Endpoints

The integration provides several API endpoints for frontend interaction:

- `POST /api/gemini-live/test` - Test connection
- `POST /api/gemini-live/stream` - Start/stop streaming
- `POST /api/gemini-live/audio` - Send audio data
- `POST /api/gemini-live/configure` - Update configuration
- `GET /api/gemini-live/status` - Get current status
- `GET /api/gemini-live/config` - Get configuration options

## Available Models

### Audio Dialog Models

- `models/gemini-2.5-flash-preview-native-audio-dialog` (Default)
- `models/gemini-2.5-pro-preview-native-audio-dialog`
- `models/gemini-2.0-flash`

### Voice Options

- **Zephyr** (Default) - Balanced, natural voice
- **Echo** - Crisp, clear articulation
- **Crystal** - Smooth, professional tone
- **Sage** - Warm, conversational style

### Response Modalities

- **AUDIO** ✅ Available now
- **VIDEO** 🔄 Coming soon (when supported by Google)

## Features

### Real-Time Streaming

The integration uses WebSocket connections for low-latency communication:

- Bidirectional audio streaming
- Real-time response generation
- Voice activity detection
- Automatic audio chunk management

### Audio Configuration

- **Sample Rate**: 16kHz (recommended), 22.05kHz, 44.1kHz
- **Input Device**: Configurable microphone selection
- **Output Device**: Configurable speaker selection
- **Audio Format**: PCM 16-bit (default)

### Error Handling

- Graceful degradation when audio hardware unavailable
- Connection retry mechanisms
- Comprehensive error reporting
- Status monitoring and alerts

## Troubleshooting

### Common Issues

#### 1. API Key Not Working

```
Error: GEMINI_API_KEY not found
```

**Solution**: Ensure your API key is properly set in environment variables or the UI.

#### 2. Audio Not Working

```
Warning: PyAudio not available
```

**Solution**: This is normal in environments without audio hardware. The integration will work for text-based interactions.

#### 3. Connection Failed

```
Error: Failed to connect to Gemini Live API
```

**Solutions**:
- Check your internet connection
- Verify API key is valid and has necessary permissions
- Ensure the selected model is available in your region

#### 4. Model Not Available

```
Error: Model not supported
```

**Solution**: Use one of the supported models listed above.

### Testing Your Setup

Run the test script to verify your integration:

```bash
python test_gemini_live_basic.py
```

This will test:
- Module imports
- Client creation
- Environment configuration
- Tool factory functions

### Debug Mode

Enable detailed logging by setting the log level:

```python
import logging
logging.getLogger('instruments.custom.gemini_live').setLevel(logging.DEBUG)
```

## Best Practices

### Performance Optimization

1. **Use appropriate sample rates**: 16kHz is recommended for voice
2. **Monitor connection status**: Check streaming status regularly
3. **Handle network interruptions**: Implement retry logic
4. **Optimize audio chunks**: Use appropriate chunk sizes for your use case

### Security Considerations

1. **Protect API keys**: Never commit API keys to version control
2. **Use environment variables**: Store sensitive configuration securely
3. **Validate inputs**: Ensure audio data is properly validated
4. **Monitor usage**: Track API usage to avoid unexpected charges

### User Experience

1. **Provide feedback**: Show connection status and streaming indicators
2. **Handle errors gracefully**: Display helpful error messages
3. **Test different voices**: Let users experiment with voice options
4. **Audio device selection**: Allow users to choose input/output devices

## Integration Examples

### Basic Streaming Session

```python
from instruments.custom.gemini_live.gemini_live_tool import GeminiLiveTool

# Create tool instance
tool = GeminiLiveTool()

# Start streaming
tool.args = {
    "action": "start_streaming",
    "voice": "Zephyr",
    "response_modalities": ["AUDIO"]
}
response = await tool.execute()
print(response.message)

# Stop streaming
tool.args = {"action": "stop_streaming"}
response = await tool.execute()
```

### Custom Voice Configuration

```python
# Configure different voice
tool.args = {
    "action": "configure",
    "voice": "Crystal",
    "response_modalities": ["AUDIO"]
}
response = await tool.execute()
```

### Status Monitoring

```python
# Check current status
tool.args = {"action": "status"}
response = await tool.execute()
print(response.message)
```

## Development Notes

### Architecture

The integration consists of several key components:

1. **GeminiLiveTool**: Main tool interface for Gary-Zero
2. **GeminiLiveClient**: WebSocket client for API communication
3. **AudioLoop**: Handles bidirectional audio streaming
4. **API Endpoints**: FastAPI routes for web UI integration
5. **UI Components**: Web interface for configuration and control

### Extension Points

The integration is designed to be extensible:

- Add new voice options by updating the configuration
- Implement video streaming when available from Google
- Extend audio processing with custom filters
- Add custom error handling and retry logic

### Contributing

When contributing to this integration:

1. Follow Gary-Zero's coding standards
2. Test with both audio and non-audio environments
3. Update documentation for new features
4. Ensure backward compatibility
5. Add appropriate error handling

## Support

For issues related to the Gemini Live API integration:

1. Check the troubleshooting section above
2. Review the test results from `test_gemini_live_basic.py`
3. Check Gary-Zero's main documentation
4. Report bugs through the project's issue tracker

## Future Enhancements

Planned improvements for the integration:

- **Video streaming support** when available from Google
- **Enhanced audio processing** with noise reduction
- **Multi-language support** for voice options
- **Custom voice training** integration
- **Advanced audio effects** and filters
- **Real-time transcription** display
- **Conversation history** with audio playback

---

*This integration brings the power of Google's Gemini Live API to Gary-Zero, enabling natural voice interactions with advanced AI capabilities.*
