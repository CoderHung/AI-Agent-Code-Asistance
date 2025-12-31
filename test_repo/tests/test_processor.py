from process_data.main import process_data

def test_sum():
    result = process_data()
    assert result["sum"] == 60
