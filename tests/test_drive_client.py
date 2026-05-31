from src.uploader import Uploader
from src.drive_client import _escape_drive_query


# Test that single quotes in folder names are properly escaped in Drive queries.
def test_single_quote_escape_filename():
    assert _escape_drive_query("O'Reilly") == "O\\'Reilly"
    
def test_no_quotes_unchanged():
    assert _escape_drive_query("NormalName") == "NormalName"

def test_multiple_quotes():
    assert _escape_drive_query("It's a 'test' folder") == "It\\'s a \\'test\\' folder"
