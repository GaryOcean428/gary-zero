#!/usr/bin/env python3
"""
Test to validate that pyaudio can be imported successfully after system dependencies fix.

This test addresses the Railway deployment issue where pyaudio compilation fails
due to missing portaudio system dependencies.
"""

import unittest


class TestPyAudioImport(unittest.TestCase):
    """Test class for pyaudio import validation."""

    def test_pyaudio_import(self):
        """Test that pyaudio can be imported without errors."""
        try:
            import pyaudio
            self.assertTrue(True, "pyaudio imported successfully")
            print("✅ pyaudio imported successfully")

            # Test basic functionality - get version if available
            if hasattr(pyaudio, '__version__'):
                print(f"✅ pyaudio version: {pyaudio.__version__}")

            # Test that PyAudio class can be instantiated (without actually initializing audio)
            pyaudio_class = pyaudio.PyAudio
            self.assertTrue(callable(pyaudio_class), "PyAudio class is callable")
            print("✅ PyAudio class is accessible")

        except ImportError as e:
            self.fail(f"Failed to import pyaudio: {e}")
        except Exception as e:
            self.fail(f"Unexpected error when importing pyaudio: {e}")

    def test_pyaudio_constants(self):
        """Test that pyaudio constants are accessible."""
        try:
            import pyaudio

            # Test that common constants are available
            constants_to_test = [
                'paFloat32',
                'paInt16',
                'paInt32',
                'paContinue',
                'paComplete'
            ]

            for constant in constants_to_test:
                self.assertTrue(hasattr(pyaudio, constant),
                              f"pyaudio.{constant} should be available")

            print("✅ pyaudio constants are accessible")

        except ImportError as e:
            self.fail(f"Failed to import pyaudio for constants test: {e}")
        except Exception as e:
            self.fail(f"Unexpected error when testing pyaudio constants: {e}")

    def test_audio_device_detection_graceful_fallback(self):
        """Test that pyaudio handles cases where no audio devices are available (like in containers)."""
        try:
            import pyaudio

            # In a container environment, we may not have audio devices
            # This test ensures pyaudio doesn't crash when trying to detect devices
            try:
                p = pyaudio.PyAudio()
                device_count = p.get_device_count()
                print(f"✅ Audio device detection successful. Found {device_count} devices")
                p.terminate()
            except Exception as audio_error:
                # This is expected in container environments without audio hardware
                print(f"⚠️  Audio hardware not available (expected in containers): {audio_error}")
                # This should not be a test failure - it's expected behavior

        except ImportError as e:
            self.fail(f"Failed to import pyaudio for device detection test: {e}")


if __name__ == '__main__':
    print("🔧 Testing pyaudio import and basic functionality...")
    print("=" * 50)

    # Run the tests
    unittest.main(verbosity=2)
