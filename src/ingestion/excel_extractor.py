import pandas as pd

def extract_tables_from_excel(file_path: str) -> list[pd.DataFrame]:
    xls = pd.ExcelFile(file_path)
    tables = []
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        df = df.dropna(how="all", axis=0).dropna(how="all", axis=1)
        if not df.empty:
            tables.append(df)
    return tables