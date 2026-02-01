import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import parse_line

def test_parse_fortigate_log_line():
    line = 'date=2023-10-12 time=10:00:00 devname="FG-100D" srcip=192.168.1.1 action=deny'
    expected = {
        'date': '2023-10-12',
        'time': '10:00:00',
        'devname': 'FG-100D',
        'srcip': '192.168.1.1',
        'action': 'deny'
    }
    assert parse_line(line) == expected

def test_parse_empty_line():
    assert parse_line("") == {}