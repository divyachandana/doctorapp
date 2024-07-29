from sqlalchemy import create_engine, inspect

DATABASE = 'sqlite:///patients.db'
engine = create_engine(DATABASE)
inspector = inspect(engine)

tables_in_db = inspector.get_table_names()
print("Tables in database:", tables_in_db)
