import psycopg2
from psycopg2 import OperationalError

def create_connection(db_name, db_user, db_password, db_host, db_port):
    connection = None
    try:
        connection = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


def create_database(connection, query):
    connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")


def execute_query(connection, query):
    # connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")


def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except OperationalError as e:
        print(f"The error '{e}' occurred")



# connection = create_connection('postgres', 'postgres','Disc!plin3','127.0.0.1','5433')

# create_database_query = "CREATE DATABASE sm_app"
# create_database(connection, create_database_query)

connection = create_connection('sm_app', 'postgres','Disc!plin3','127.0.0.1','5433')


create_users_table = """
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL, 
  age INTEGER,
  gender TEXT,
  nationality TEXT
)
"""

execute_query(connection, create_users_table)

create_posts_table = """
CREATE TABLE IF NOT EXISTS posts (
  id SERIAL PRIMARY KEY, 
  title TEXT NOT NULL, 
  description TEXT NOT NULL, 
  user_id INTEGER REFERENCES users(id)
)
"""

execute_query(connection, create_posts_table)

'''
users = [
    ("James", 25, "male", "USA"),
    ("Leila", 32, "female", "France"),
    ("Brigitte", 35, "female", "England"),
    ("Mike", 40, "male", "Denmark"),
    ("Elizabeth", 21, "female", "Canada"),
]

user_records = ", ".join(["%s"] * len(users))

insert_users = (
    f"INSERT INTO users (name, age, gender, nationality) VALUES {user_records}"
)

posts = [
    ("Happy", "I am feeling very happy today", 1),
    ("Hot Weather", "The weather is very hot today", 2),
    ("Help", "I need some help with my work", 2),
    ("Great News", "I am getting married", 1),
    ("Interesting Game", "It was a fantastic game of tennis", 5),
    ("Party", "Anyone up for a late-night party today?", 3),
]

post_records = ", ".join(["%s"] * len(posts))

insert_posts = (
    f"INSERT INTO posts (title, description, user_id) VALUES {post_records}"
)


connection.autocommit = True
cursor = connection.cursor()
cursor.execute(insert_users, users)
cursor.execute(insert_posts, posts)
'''

select_users = "SELECT * from users"
users = execute_read_query(connection, select_users)

for user in users:
    print(user)
'''
update_post_description = """
UPDATE
  posts
SET
  description = 'The weather has become pleasant now'
WHERE
  id = 2
"""

execute_query(connection, update_post_description)
'''

select_posts = "SELECT * from posts"
posts = execute_read_query(connection, select_posts)

for post in posts:
    print(post)

# delete_comment = "DELETE FROM comments WHERE id = 2"
# execute_query(connection, delete_comment)

create_comments_table = """
CREATE TABLE IF NOT EXISTS comments (
  id SERIAL PRIMARY KEY, 
  text TEXT NOT NULL, 
  user_id INTEGER NOT NULL, 
  post_id INTEGER NOT NULL, 
  FOREIGN KEY (user_id) REFERENCES users (id),
  FOREIGN KEY (post_id) REFERENCES posts (id)
);
"""

create_likes_table = """
CREATE TABLE IF NOT EXISTS likes (
  id SERIAL PRIMARY KEY, 
  user_id INTEGER NOT NULL, 
  post_id integer NOT NULL, 
  FOREIGN KEY (user_id) REFERENCES users (id),
  FOREIGN KEY (post_id) REFERENCES posts (id)
);
"""

execute_query(connection, create_comments_table)
execute_query(connection, create_likes_table)

connection.commit()