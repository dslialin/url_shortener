import string
import pytest

from app.main import generate_short_code 

def test_generate_short_code_properties():
    default_length = 6
    short_code = generate_short_code(default_length)

    assert isinstance(short_code, str)
    assert len(short_code) == default_length

    allowed_chars = string.ascii_letters + string.digits
    assert all(char in allowed_chars for char in short_code)

def test_generate_short_code_custom_length():
    custom_length = 10
    short_code = generate_short_code(custom_length)

    assert isinstance(short_code, str)
    assert len(short_code) == custom_length

    allowed_chars = string.ascii_letters + string.digits
    assert all(char in allowed_chars for char in short_code) 