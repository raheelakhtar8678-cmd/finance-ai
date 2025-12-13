def test_numeric_conversion():
    df = pd.DataFrame({
        " Amount ": ["1,000", "(200)", "300"]
    })

    cleaned = clean_all_tables([df])[0]

    assert cleaned["amount"].iloc[0] == 1000.0
    assert cleaned["amount"].iloc[1] == -200.0
    assert cleaned["amount"].iloc[2] == 300.0
    assert cleaned["amount"].dtype == "float64"