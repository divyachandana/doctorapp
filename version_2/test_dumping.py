from sqlalchemy import text, create_engine

tables = ['allergies', 'careplans', 'conditions', 'encounters', 'immunizations', 'medications', 'observations', 'patients', 'procedures']

DATABASE = 'sqlite:///patients.db'
engine = create_engine(DATABASE)

def clean_name(name):
    # Keep only alphabetic characters
    cleaned_name = ''.join(filter(str.isalpha, name))
    return cleaned_name

for t in tables:
    if t == 'patients':
        query = text(f"SELECT ID, FIRST, LAST FROM {t}")

        with engine.connect() as connection:
            result = connection.execute(query).fetchall()
            for row in result:
                id, first, last = row[0], row[1], row[2]

                if first is None or last is None:
                    # Remove row if any of the names are None
                    delete_query = text(f"DELETE FROM {t} WHERE ID = :id")
                    connection.execute(delete_query, {'id': id})  # Corrected here
                else:
                    cleaned_first = clean_name(first)
                    cleaned_last = clean_name(last)
                    
                    # Update the cleaned names back to the table
                    update_query = text(f"""
                        UPDATE {t}
                        SET FIRST = :first, LAST = :last
                        WHERE ID = :id
                    """)
                    connection.execute(update_query, {'first': cleaned_first, 'last': cleaned_last, 'id': id})

            print(f"Cleaned data in table {t}.")
