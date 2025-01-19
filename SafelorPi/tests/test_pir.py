import sys
import pytest
from unittest.mock import MagicMock, patch

sys.modules['RPi'] = MagicMock()
sys.modules['RPi.GPIO'] = MagicMock()

from sensors.pir import PIRSensor

@pytest.fixture
def pir_sensor():
    with patch('sensors.pir.GPIO') as mock_gpio:
        mock_gpio.BOARD = 'BOARD'
        mock_gpio.IN = 'IN'
        mock_gpio.input.return_value = False
        sensor = PIRSensor(pin=11)
        yield sensor
        sensor.cleanup()

def test_pir_sensor_initialization():
    with patch('sensors.pir.GPIO') as mock_gpio:
        mock_gpio.BOARD = 'BOARD'
        mock_gpio.IN = 'IN'
        sensor = PIRSensor(pin=11)
        mock_gpio.setmode.assert_called_once_with(mock_gpio.BOARD)
        mock_gpio.setup.assert_called_once_with(11, mock_gpio.IN)

def test_is_triggered_when_motion_detected(pir_sensor):
    with patch('sensors.pir.GPIO') as mock_gpio:
        mock_gpio.input.return_value = True
        assert pir_sensor.is_triggered() is True

def test_is_triggered_when_no_motion(pir_sensor):
    with patch('sensors.pir.GPIO') as mock_gpio:
        mock_gpio.input.return_value = False
        assert pir_sensor.is_triggered() is False

def test_cleanup(pir_sensor):
    with patch('sensors.pir.GPIO') as mock_gpio:
        pir_sensor.cleanup()
        mock_gpio.cleanup.assert_called_once()
