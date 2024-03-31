import pyodbc
import config

conn = pyodbc.connect(config.connectionString)

name = str(input("Enter Player Name: "))

cursor = conn.cursor()
SQL_QUERY = "Select * from espn where Player_Name ='" + name + "'"

cursor.execute(SQL_QUERY)

records = cursor.fetchall()
num_rows = len(records)

if num_rows == 1:
    print(records[0].team)
else:
    for r in records:
        if r.team == 'TOT':
            print(f"{r.Rank}\t{r.Player_Name}\t{r.field_goals}")