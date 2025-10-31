from mf.extract.ecb_fx import fetch_eur_usd


def test_usdeur_identity_live():
    df = fetch_eur_usd("2025-10-01", "2025-10-10")
    assert not df.empty, "ECB fetch returned empty DataFrame"

    cols = {"date", "eurusd", "usdeur", "source"}
    assert cols.issubset(df.columns), f"Missing columns: {cols - set(df.columns)}"

    assert (df["eurusd"] > 0).all(), "eurusd must be > 0"
    assert (df["usdeur"] > 0).all(), "usdeur must be > 0"

    prod = (df["eurusd"] * df["usdeur"]).astype(float)
    max_err = (prod - 1.0).abs().max()
    assert max_err < 1e-9, f"max |eurusd*usdeur - 1| = {max_err}"
