# Pytest Unit Test Plan for midi-macro

This document outlines a comprehensive testing strategy for the midi-macro project.

## Testing Philosophy

**Goal**: Achieve high test coverage for business logic while acknowledging that hardware-dependent components (MIDI I/O, audio playback) require integration testing.

**Approach**: 
- Unit tests for pure logic (bank management, configuration parsing, action execution)
- Mock-based tests for external dependencies (MIDI, audio, HTTP, keyboard)
- Integration tests marked with `@pytest.mark.integration` for hardware testing

## Phase 1: Test Infrastructure Setup

### 1.1 Directory Structure
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and mocks
├── unit/
│   ├── __init__.py
│   ├── test_bank_manager.py
│   ├── test_action_runner.py
│   ├── test_soundboard.py
│   └── test_config.py
├── integration/
│   ├── __init__.py
│   └── test_midi_hardware.py
└── fixtures/
    ├── config/
    │   ├── main.yaml
│   │   └── banks/
│   │       ├── test_bank.yaml
│   │       └── empty_bank.yaml
│   └── sounds/
│       └── test_sound.wav
```

### 1.2 Dependencies to Add
```bash
uv add --dev pytest pytest-cov pytest-mock
```

### 1.3 pytest Configuration (pyproject.toml)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "--strict-markers",
]
markers = [
    "integration: marks tests as integration tests (requires hardware)",
    "slow: marks tests as slow",
]
```

## Phase 2: Unit Test Implementation

### 2.1 Bank Manager Tests (`tests/unit/test_bank_manager.py`)

**Test Coverage Target**: 95%

```python
# Test 1: Bank initialization
- test_default_bank_is_a()
- test_bank_notes_constant_structure()

# Test 2: Bank switching via MIDI
- test_bank_switch_note_on_channel_4()
- test_bank_switch_a_to_b()
- test_bank_switch_b_to_c()
- test_bank_switch_c_to_d()
- test_bank_switch_d_to_a()
- test_invalid_bank_note_ignored()

# Test 3: Grid button detection and normalization
- test_bank_a_grid_buttons_36_to_51()
- test_bank_b_grid_buttons_52_to_67()
- test_bank_c_grid_buttons_68_to_83()
- test_bank_d_grid_buttons_84_to_99()
- test_note_normalization_0_to_15()
- test_out_of_range_notes_ignored()

# Test 4: Callbacks
- test_bank_callback_triggered_on_switch()
- test_button_callback_triggered_on_press()
- test_callbacks_not_triggered_on_same_bank()
- test_no_callback_when_none_provided()

# Test 5: Thread safety
- test_concurrent_bank_switches()
- test_concurrent_button_presses()

# Test 6: Edge cases
- test_velocity_zero_ignored()
- test_note_off_ignored()
- test_wrong_channel_ignored()
```

### 2.2 Action Runner Tests (`tests/unit/test_action_runner.py`)

**Test Coverage Target**: 90%

```python
# Test 1: Script execution
- test_run_script_with_relative_path()
- test_run_script_with_absolute_path()
- test_run_python_script()
- test_run_bash_script()
- test_script_with_args()
- test_script_not_found()
- test_script_execution_failure()
- test_blocking_script_execution()
- test_non_blocking_script_execution()
- test_script_cleanup_terminates_processes()

# Test 2: Webhook execution
- test_webhook_post_request()
- test_webhook_get_request()
- test_webhook_with_headers()
- test_webhook_with_body()
- test_webhook_missing_url()
- test_webhook_http_error()
- test_webhook_unsupported_method()
- test_webhook_httpx_not_installed()

# Test 3: Keyboard execution
- test_keyboard_single_key()
- test_keyboard_modifier_combo()
- test_keyboard_multiple_modifiers()
- test_keyboard_special_keys()
- test_keyboard_missing_shortcut()
- test_keyboard_pynput_not_installed()

# Test 4: Action routing
- test_execute_script_action()
- test_execute_webhook_action()
- test_execute_keyboard_action()
- test_execute_unknown_action()
- test_execute_missing_type()
```

### 2.3 Configuration Tests (`tests/unit/test_config.py`)

**Test Coverage Target**: 95%

```python
# Test 1: Main config loading
- test_load_main_yaml_exists()
- test_load_main_yaml_missing()
- test_load_main_yaml_invalid()

# Test 2: Bank config loading
- test_load_bank_configs()
- test_load_empty_bank_d()
- test_load_missing_bank_file()
- test_merge_sounds_from_multiple_banks()

# Test 3: Configuration structure
- test_midi_config_structure()
- test_sound_config_structure()
- test_button_mapping_structure()
- test_action_config_structure()

# Test 4: Path resolution
- test_relative_path_resolution()
- test_absolute_path_resolution()
```

### 2.4 Soundboard Tests (`tests/unit/test_soundboard.py`)

**Test Coverage Target**: 80% (audio playback is hardware-dependent)

```python
# Test 1: Sound loading (mocked)
- test_load_sound_file_exists()
- test_load_sound_file_not_found()
- test_load_sound_invalid_format()
- test_load_mono_sound_converts_to_stereo()
- test_load_sound_with_volume()

# Test 2: Bank mappings
- test_build_button_mappings()
- test_build_mappings_with_invalid_sound()
- test_build_mappings_legacy_format()

# Test 3: Resampling
- test_resample_same_rate_no_change()
- test_resample_48k_to_44k()
- test_resample_22k_to_44k()

# Test 4: Audio data structures
- test_active_sound_tuple_structure()
- test_sounds_dict_structure()

# Test 5: Play logic
- test_play_existing_sound()
- test_play_nonexistent_bank()
- test_play_nonexistent_note()
- test_play_toggle_restarts_sound()
```

## Phase 3: Mock Fixtures (conftest.py)

### 3.1 MIDI Mocks
```python
@pytest.fixture
def mock_mido_message():
    """Create a mock mido Message."""
    def _create(msg_type, channel, note, velocity):
        msg = MagicMock()
        msg.type = msg_type
        msg.channel = channel
        msg.note = note
        msg.velocity = velocity
        return msg
    return _create

@pytest.fixture
def mock_midi_port():
    """Mock mido input/output port."""
    with patch('mido.open_input') as mock:
        yield mock
```

### 3.2 Audio Mocks
```python
@pytest.fixture
def mock_soundfile():
    """Mock soundfile.read."""
    with patch('soundfile.read') as mock:
        # Return stereo 44.1kHz audio data
        mock.return_value = (
            np.zeros((44100, 2), dtype=np.float32),
            44100
        )
        yield mock

@pytest.fixture
def mock_sounddevice():
    """Mock sounddevice OutputStream."""
    with patch('sounddevice.OutputStream') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance
```

### 3.3 HTTP Mocks
```python
@pytest.fixture
def mock_httpx():
    """Mock httpx requests."""
    with patch('httpx.post') as mock_post, \
         patch('httpx.get') as mock_get:
        yield {'post': mock_post, 'get': mock_get}
```

### 3.4 Keyboard Mocks
```python
@pytest.fixture
def mock_keyboard():
    """Mock pynput keyboard controller."""
    with patch('pynput.keyboard.Controller') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance
```

### 3.5 Configuration Fixtures
```python
@pytest.fixture
def test_sounds_config():
    """Sample sounds configuration."""
    return {
        'test_sound': {'file': 'sounds/test.wav', 'volume': 1.0},
        'another_sound': {'file': 'sounds/another.wav', 'volume': 0.8},
    }

@pytest.fixture
def test_banks_config():
    """Sample banks configuration."""
    return {
        'A': {
            '0': {'sound': 'test_sound'},
            '1': {'sound': 'another_sound', 'volume': 0.5},
        },
        'B': {
            '0': 'test_sound',  # Legacy format
        }
    }

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory with test files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Create main.yaml
    main_yaml = config_dir / "main.yaml"
    main_yaml.write_text("""
midi:
  port_name: "Test Port"
  grid_channel: 1
  bank_channel: 2
banks:
  A: config/banks/test.yaml
  B: null
""")
    
    # Create banks directory
    banks_dir = config_dir / "banks"
    banks_dir.mkdir()
    
    # Create test bank
    test_bank = banks_dir / "test.yaml"
    test_bank.write_text("""
sounds:
  test_sound:
    file: sounds/test.wav
mappings:
  0:
    sound: test_sound
""")
    
    return config_dir
```

## Phase 4: Integration Tests

### 4.1 MIDI Hardware Tests (marked with `@pytest.mark.integration`)
```python
@pytest.mark.integration
class TestMIDIHardware:
    """Tests requiring actual Midi Fighter 3D hardware."""
    
    def test_midi_port_discovery(self):
        """Verify MF3D port is available."""
        
    def test_note_on_message_reception(self):
        """Press a button and verify note_on received."""
        
    def test_bank_switch_message(self):
        """Press bank switch and verify channel 4 message."""
        
    def test_led_output(self):
        """Send note_on to controller and verify LED lights."""
```

### 4.2 Audio Hardware Tests
```python
@pytest.mark.integration
@pytest.mark.slow
class TestAudioHardware:
    """Tests requiring audio hardware."""
    
    def test_audio_stream_creation(self):
        """Verify ALSA stream can be created."""
        
    def test_sound_playback(self):
        """Play a test sound and verify output."""
```

## Phase 5: Test Execution Strategy

### 5.1 Running Tests
```bash
# Run all unit tests
pytest tests/unit/

# Run with coverage
pytest --cov=src tests/unit/

# Run integration tests only
pytest -m integration

# Run all tests including integration
pytest -m "integration or not integration"

# Run specific test file
pytest tests/unit/test_bank_manager.py

# Run single test
pytest tests/unit/test_bank_manager.py::test_default_bank_is_a

# Run with verbose output
pytest -v
```

### 5.2 CI/CD Integration
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: uv sync
      - run: uv run pytest tests/unit/ --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Phase 6: Coverage Goals

| Module | Target Coverage | Priority |
|--------|----------------|----------|
| bank_manager.py | 95% | High |
| action_runner.py | 90% | High |
| types.py | 100% | Medium |
| main.py | 70% | Medium |
| midi_handler.py | 60% | Low (hardware-dependent) |
| soundboard.py | 80% | Medium |

## Phase 7: Implementation Order

1. **Week 1**: Set up test infrastructure (conftest.py, fixtures, config)
2. **Week 2**: Bank manager tests (highest ROI - pure logic)
3. **Week 3**: Action runner tests (complex mocking)
4. **Week 4**: Configuration tests
5. **Week 5**: Soundboard tests (audio mocking)
6. **Week 6**: Integration test framework
7. **Week 7**: Coverage improvement and edge cases
8. **Week 8**: CI/CD integration

## Key Testing Challenges & Solutions

### Challenge 1: MIDI Hardware Dependency
**Solution**: Abstract MIDI behind interface, mock for unit tests, integration tests for hardware.

### Challenge 2: Audio ALSA Dependencies
**Solution**: Mock sounddevice and soundfile, test logic separately from audio I/O.

### Challenge 3: External HTTP Calls
**Solution**: Use pytest-mock to intercept httpx calls, verify request structure.

### Challenge 4: Keyboard Injection
**Solution**: Mock pynput, verify key sequences are correct.

### Challenge 5: Threading in Soundboard
**Solution**: Test mixer logic without starting threads, mock threading components.

## Success Metrics

- Unit test coverage >= 85%
- All critical paths tested (bank switching, action execution)
- Integration tests for hardware validation
- CI/CD pipeline running tests on every PR
- Documentation updated with testing guidelines
