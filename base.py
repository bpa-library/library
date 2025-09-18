# db = 'MySQL'
# db = 'postgreSQL'

import os
from dotenv import load_dotenv

load_dotenv()
DB_TYPE = os.getenv('DB_TYPE').lower()   # MySQL / postgreSQL
# db = os.getenv('DB_TYPE').lower()

# Connect to Railway MySQL
# import mysql.connector

def MySQL_db():
    try:
        from urllib.parse import urlparse
        from mysql.connector import connect

        db_url = os.getenv('mysql_DATABASE_URL')
        if not db_url:
            print("❌ MySQL database URL not found")
            return False
        
        parsed_url = urlparse(db_url)

        config = {
            'host': parsed_url.hostname,
            'port': parsed_url.port,
            'user': parsed_url.username,
            'password': parsed_url.password,
            'database': parsed_url.path[1:],  # Remove leading slash
            'charset': 'utf8mb4',
            'autocommit': True
        }
        connection = connect(**config)
        # print("✅ MySQL connection successful!")
        return connection
        # return mysql.connector.connect(os.getenv('mysql_DATABASE_URL'))
    except Exception as e:
        print(f"❌ DB Error - MySQL: {str(e)}")
        return False
    

# def MySQL_db():
#     try:
#         return mysql.connector.connect(
#             host=os.getenv('DB_HOST'),
#             user=os.getenv('DB_USER'),
#             password=os.getenv('DB_PASSWORD'),
#             database=os.getenv('DB_NAME'),
#             port=int(os.getenv('DB_PORT'))
#         )
#     except Exception as e:
#         print(f"❌ DB Error - MySQL: {str(e)}")
#         return False


# PostgreSQL - Free Forever - https://neon.com/ - (Neon.tech)
# Free Limit 3GB storage, Beyond Free $0.10/GB
from sqlalchemy import create_engine, text
import psycopg2
from psycopg2.extras import execute_values
from urllib.parse import urlparse
            

def postgreSQL_db_old():
    DATABASE_URL = os.getenv('postgresql_DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("Database URL not found. Please set postgresql_DATABASE_URL environment variable.")

    engine = create_engine(DATABASE_URL)
    try:
        return engine
    except Exception as e:
        print(f"DB Error - postgreSQL: {str(e)}")
        return False
    
def postgreSQL_db():
    DATABASE_URL = os.getenv('postgresql_DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("Database URL not found. Please set postgresql_DATABASE_URL environment variable.")

    try:
        import psycopg2
        connection = psycopg2.connect(DATABASE_URL)
        return connection
        # result = urlparse(DATABASE_URL)
        # engine = create_engine(DATABASE_URL)

    # try:
    #     return psycopg2.connect(
    #         host=result.hostname,
    #         database=result.path[1:],  # Remove leading '/'
    #         user=result.username,
    #         password=result.password,
    #         port=result.port
    #     )
    except Exception as e:
        print(f"❌ DB Error - postgreSQL: {str(e)}")
        return False

def conn():
    if DB_TYPE == 'mysql':
    # if db == 'MySQL':
        try:
            connection = MySQL_db()
            if connection is None or connection is False:
                raise ConnectionError("Failed to connect to MySQL. Check credentials and network.")
            cursor = connection.cursor(dictionary=True)
            return cursor, connection
        except Exception as e:
            print(f"❌ DB Error - conn() - MySQL: {str(e)} Might be 'Trial expired'.")
            raise Exception("MySQL is not available.")
    elif DB_TYPE == 'postgresql':
    # elif db == 'postgreSQL':
        try:
            connection = postgreSQL_db()
            if connection is None or connection is False:
                raise ConnectionError("Failed to connect to PostgreSQL. Check credentials and network.")
            from psycopg2.extras import DictCursor
            cursor = connection.cursor(cursor_factory=DictCursor)
            return cursor, connection
        except Exception as e:
            print(f"❌ DB Error - conn() - postgreSQL: {str(e)}")
            raise Exception("PostgreSQL is not available.")
    else:
        raise ValueError(f"Unknown database type: {DB_TYPE}")
    
def conn_old():
    if DB_TYPE == 'mysql':
    # if db == 'MySQL':
        connection = MySQL_db()
        if connection is None:
            raise ConnectionError("Failed to connect to MySQL. Check credentials and network.")
        cursor = connection.cursor()
        return cursor, connection
    elif DB_TYPE == 'postgresql':
    # elif db == 'postgreSQL':
        engine = postgreSQL_db()
        if not engine:
            raise ConnectionError("Failed to connect to PostgreSQL. Check credentials and network.")
        connection = engine.connect()
        return connection, engine

def db_select(query, params=None):
    if DB_TYPE == 'mysql':
    # if db == 'MySQL':
        cursor, connection = conn()
        try:
            if params is not None:
                if not isinstance(params, (tuple, list, dict)):
                    params = (params,)
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"❌ MySQL SELECT Error: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
            
    elif DB_TYPE == 'postgresql':
    # elif db == 'postgreSQL':
        cursor, connection = conn()
        try:       
            # >>> cur.execute("select * from test order by id")
            # >>> cur.fetchall()
            # [(1, 20, 3), (4, 50, 6), (7, 8, 9)])
            # query = "SELECT name FROM categories WHERE id = :p1"
            # params = {'p1': 1} # MySQL
            # params = {'p1': 494} # postgeSQL
                        
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"❌ PostgreSQL SELECT Error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

def db_select_old(query, params=None):
    if DB_TYPE == 'mysql':
    # if db == 'MySQL':
        cursor, connection = conn()
        try:
            if params is not None:
                if not isinstance(params, (tuple, list, dict)):
                    params = (params,)
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"❌ MySQL SELECT Error: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
            
    elif DB_TYPE == 'postgresql':
    # elif db == 'postgreSQL':
        connection, engine = conn()
        try:
            if isinstance(query, str):
                query = text(query)
                
            if params:
                result = connection.execute(query, params)
            else:
                result = connection.execute(query)
            
            results = result.fetchall()
            return results
        except Exception as e:
            print(f"❌ PostgreSQL SELECT Error: {e}")
            return None
        finally:
            connection.close()

def universal_db_select(query, params=None):
    # Use the unified DB_TYPE variable
    if DB_TYPE == 'mysql':
    # if db == 'MySQL':
        # Convert named parameters to MySQL format
        if isinstance(params, dict):
            param_values = tuple(params.values())
            for key in params.keys():
                query = query.replace(f':{key}', '%s')
            params = param_values
        
        cursor, connection = conn()
        try:
            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"❌ MySQL SELECT Error: {e}")
            return []
        finally:
            cursor.close()
            connection.close()

            # Convert to list of dictionaries for consistency
        #     columns = [col[0] for col in cursor.description] if cursor.description else []
        #     results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        #     return results
        # except Exception as e:
        #     print(f"❌ MySQL SELECT Error: {e}")
        #     return None
        # finally:
        #     cursor.close()
        #     connection.close()
            
    elif DB_TYPE == 'postgresql':
    # elif db == 'postgreSQL':
        cursor, connection = conn()
        # connection, engine = conn()
        try:   
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()

            # Convert to list of dictionaries for consistency
            return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ PostgreSQL SELECT Error: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    else:
        print(f"❌ Unknown database type: {DB_TYPE}")
        return []

def db_insert(query, params=None, batch_data=None):
    if DB_TYPE == 'mysql':
        cursor, connection = conn()
        try:
            if params is not None:
                if not isinstance(params, (tuple, list, dict)):
                    params = (params,)
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            connection.commit()
            
            # For MySQL, return the last insert ID if available
            if query.strip().lower().startswith('insert'):
                return cursor.lastrowid  # This returns the auto-generated ID
            else:
                return cursor.rowcount
                
        except Exception as e:
            print(f"❌ MySQL INSERT Error: {e}")
            connection.rollback()
            return None
        finally:
            cursor.close()
            connection.close()

    elif DB_TYPE == 'postgresql':
        cursor, connection = conn()
        try:
            if batch_data:
                from psycopg2.extras import execute_values
                execute_values(cursor, query, batch_data)
                connection.commit()
                return len(batch_data)
            elif params:
                cursor.execute(query, params)
                connection.commit()
                
                # For PostgreSQL with RETURNING clause, return the ID
                if 'returning' in query.lower():
                    result = cursor.fetchone()
                    if result:
                        return result[0]
                return cursor.rowcount
            else:
                cursor.execute(query)
                connection.commit()
                return cursor.rowcount
                
        except Exception as e:
            print(f"❌ PostgreSQL INSERT Error: {e}")
            if connection:
                connection.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    else:
        print(f"❌ Unknown database type: {DB_TYPE}")
        return None

def db_insert_old2(query, params=None, batch_data=None):
    if DB_TYPE == 'mysql':
    # if db == 'MySQL':
        cursor, connection = conn()
        try:
            if params is not None:
                if not isinstance(params, (tuple, list, dict)):
                    params = (params,)
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            connection.commit()
            
            # For MySQL, return the last insert ID if available
            if query.strip().lower().startswith('insert'):
                return cursor.lastrowid  # This returns the auto-generated ID
            else:
                return cursor.rowcount
                
        except Exception as e:
            print(f"❌ MySQL INSERT Error: {e}")
            connection.rollback()
            return None
        finally:
            cursor.close()
            connection.close()

    elif DB_TYPE == 'postgresql':
    # elif db == 'postgreSQL':
        cursor, connection = conn()
        try:
            if batch_data:
                from psycopg2.extras import execute_values
                execute_values(cursor, query, batch_data)
                connection.commit()
                return len(batch_data)
            elif params:
                cursor.execute(query, params)
                connection.commit()
                
                # For PostgreSQL with RETURNING clause, return the ID
                if 'returning' in query.lower():
                    result = cursor.fetchone()
                    if result:
                        return result[0]
                return cursor.rowcount
            else:
                cursor.execute(query)
                connection.commit()
                return cursor.rowcount
                
        except Exception as e:
            print(f"❌ PostgreSQL INSERT Error: {e}")
            if connection:
                connection.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    else:
        print(f"❌ Unknown database type: {DB_TYPE}")
        return None

def universal_db_select_old(query, params=None):
    if DB_TYPE == 'mysql':
    # if db == 'MySQL':
        # Convert named parameters to MySQL format
        if isinstance(params, dict):
            # Convert {:p1: 494} to (494,)
            param_values = tuple(params.values())
            # Convert :p1 to %s
            for key in params.keys():
                query = query.replace(f':{key}', '%s')
            params = param_values
        
        cursor, connection = conn()
        try:
            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"❌ MySQL SELECT Error: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
            
    elif DB_TYPE == 'postgresql':
    # elif db == 'postgreSQL':
        connection, engine = conn()
        try:
            if isinstance(query, str):
                query = text(query)
                
            if params:
                result = connection.execute(query, params)
            else:
                result = connection.execute(query)
            
            results = result.fetchall()
            return results
        except Exception as e:
            print(f"❌ PostgreSQL SELECT Error: {e}")
            return None
        finally:
            connection.close()

def db_execute(query, params=None):
    """Universal function for executing DDL statements (CREATE, DROP, ALTER)"""
    if DB_TYPE == 'mysql':
    # if db == 'MySQL':
        cursor, connection = conn()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            connection.commit()
            return True
        except Exception as e:
            print(f"❌ MySQL Execute Error: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

    elif DB_TYPE == 'postgresql':
    # elif db == 'postgreSQL':
        cursor, connection = conn()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            connection.commit()
            return True
        except Exception as e:
            print(f"❌ PostgreSQL Execute Error: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

# def db_create(create):
#     if db == 'MySQL':
#         cursor, connection = conn()
#         cursor.execute(create)
#         print("✅ MySQL: Table created successfully!")
#     elif db == 'postgreSQL':
#         connection, engine = conn()
#         trans = connection.begin()
#         try:
#             connection.execute(create)
#             trans.commit()
#             print("✅ PostgreSQL: Table created successfully!")
#         except Exception as e:
#             trans.rollback()
#             print(f"❌ PostgreSQL error: {e}")
#         finally:
#             connection.close()

def db_insert_old(query, params=None):
    if DB_TYPE == 'mysql':
    # if db == 'MySQL':
        cursor, connection = conn()
        try:
            if params is not None:
                if not isinstance(params, (tuple, list, dict)):
                    params = (params,)
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rowcount = cursor.rowcount
            
            connection.commit()
            return rowcount
        except Exception as e:
            print(f"❌ MySQL INSERT Error: {e}")
            return None
        finally:
            cursor.close()
            connection.close()

    elif DB_TYPE == 'postgresql':
    # elif db == 'postgreSQL':
        connection, engine = conn()
        try:
            if isinstance(query, str):
                query = text(query)
                
            trans = connection.begin()
            if params:
                result = connection.execute(query, params)
            else:
                result = connection.execute(query)
            trans.commit()
            
            return result.rowcount
            # return result.rowcount, connection, engine
        except Exception as e:
            print(f"❌ PostgreSQL INSERT Error: {e}")
            return None, None, None 
        finally:
            connection.close()

# def db_insert2(query, batch=None):
def db_insert(query, params=None, batch_data=None):
    if DB_TYPE == 'mysql':
    # if db == 'MySQL':
        cursor, connection = conn()
        try:
            if params is not None:
                if not isinstance(params, (tuple, list, dict)):
                    params = (params,)
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            connection.commit()
            return cursor.rowcount
        except Exception as e:
            print(f"❌ MySQL INSERT Error: {e}")
            connection.rollback()  # Rollback on connection
            return None
        finally:
            cursor.close()
            connection.close()

    elif DB_TYPE == 'postgresql':
    # elif db == 'postgreSQL':
        cursor, connection = conn()
        try:
            if batch_data:
                # Use psycopg2's execute_values for efficient batch insert  
                execute_values(cursor, query, batch_data)
                connection.commit()
                return len(batch_data)
            elif params:
                cursor.execute(query, params)
                connection.commit()
                return cursor.rowcount
            else:
                cursor.execute(query)
                connection.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"❌ PostgreSQL INSERT Error: {e}")
            if connection:  # Rollback on connection, not cursor
                connection.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()




