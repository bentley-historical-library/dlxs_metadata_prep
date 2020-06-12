import csv
import os
import pyodbc


def export_identifiers(DLXSMetadataPrepper):
    collection_id = DLXSMetadataPrepper.collection_id
    collection_dir = DLXSMetadataPrepper.collection_dir
    digitization_identifiers_csv = os.path.join(collection_dir, "digitization_db_items.csv")

    server = "url.for.digitization.server"
    database = "digitization"
    cnxn = pyodbc.connect(r'Driver={ODBC Driver 13 for SQL Server};Server=' +
                        server + ';Database=' + database + ';Trusted_Connection=yes')
    cursor = cnxn.cursor()

    sql = """SELECT Item_Identifier, ASpaceURI from Items WHERE Collection_ID=?"""
    params = [collection_id]
    results = cursor.execute(sql, params)
    headers = ["identifier", "aspace_uri"]
    with open(digitization_identifiers_csv, "wb") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(results.fetchall())
