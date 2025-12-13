import re
import pandas as pd


# ==========================================================
# 0. Utility: detect if header row is actually data
# ==========================================================
def header_is_data(df: pd.DataFrame) -> bool:
    """
    True if first row looks like numeric data rather than actual column names.
    Used to avoid mis-detecting a header on CSV/XLSX files.
    """
    first_row = df.iloc[0]
    numeric_like = 0

    for x in first_row:
        if isinstance(x, (int, float)):
            numeric_like += 1
        if isinstance(x, str) and re.fullmatch(r"\(?\d+[\d,]*\)?", x):
            numeric_like += 1

    # If most values look numeric → don't treat first row as header
    return numeric_like < len(first_row) / 2


# ==========================================================
# 1. Strip commas
# ==========================================================
def strip_commas(df: pd.DataFrame) -> pd.DataFrame:
    return df.map(lambda x: x.replace(",", "") if isinstance(x, str) else x)


# ==========================================================
# 2. Parentheses negative conversion (returns STRING!)
# ==========================================================
def parentheses_to_negative(df: pd.DataFrame) -> pd.DataFrame:
    def convert(x):
        if isinstance(x, str) and re.fullmatch(r"\(\s*\d+[\d,]*\s*\)", x):
            # "(1200)" -> "-1200"
            x = x.strip("()").replace(",", "")
            return f"-{x}"
        return x

    return df.map(convert)


# ==========================================================
# 3. Header normalization
# ==========================================================
def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    new_cols = []
    seen = set()
    for col in df.columns:
        c = str(col).strip().lower()
        c = c.replace("(", "_").replace(")", "_")
        c = re.sub(r"[^a-z0-9]+", "_", c)
        c = re.sub(r"_+", "_", c).strip("_")
        # Make unique
        final = c
        counter = 1
        while final in seen:
            final = f"{c}_{counter}"
            counter += 1
        seen.add(final)
        new_cols.append(final)
    df.columns = new_cols
    return df


# ==========================================================
# 4. Auto detect header SAFELY (with test condition fixed)
# ==========================================================
def auto_detect_header(df: pd.DataFrame) -> pd.DataFrame:
    """
    Only use row 0 as header if:
    - current headers look like unnamed (0, 1, 2...)
    - AND first row looks like text, not numbers
    """
    # detect unnamed columns
    if all(re.fullmatch(r"unnamed.*", str(c).lower()) or isinstance(c, int) for c in df.columns):
        if header_is_data(df):
            df.columns = df.iloc[0]
            df = df.drop(0).reset_index(drop=True)

    return df


# ==========================================================
# 5. Drop empty rows/cols
# ==========================================================
def drop_empty(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(how="all", axis=0).dropna(how="all", axis=1)


# ==========================================================
# 6. Safe numeric (NO WARNING)
# ==========================================================
def safe_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert object columns to numeric where possible.
    Handles duplicate columns safely.
    """
    for col in df.columns:
        series = df[col]
        # If column is ambiguous (returns DataFrame), skip
        if isinstance(series, pd.DataFrame):
            continue
        if series.dtype == object:
            # Try conversion, keep original if failure
            converted = pd.to_numeric(series, errors="ignore")
            df[col] = converted
    return df

# ==========================================================
# 7. Full cleaning
# ==========================================================
def clean_table(df: pd.DataFrame) -> pd.DataFrame:
    df = auto_detect_header(df)
    df = normalize_headers(df)
    df = strip_commas(df)
    df = parentheses_to_negative(df)
    df = safe_numeric(df)
    df = drop_empty(df)
    return df


def clean_all_tables(table_list: list[pd.DataFrame]) -> list[pd.DataFrame]:
    return [clean_table(df.copy()) for df in table_list]