import csv 
"""
`users` is a global dictionary that stores the user data. The key is the username of the user
and the value is an array of the user's pending messages as strings. So for example,
if the user "bob" has pending messages "hello" and "goodbye", then `users` will be:
{
    "bob": ["hello", "goodbye"]
}
"""
default_db_name = "users"


def init_db(database_name: str = default_db_name) -> None:
    """
    Creates database file `database_name`.csv if it exists, otherwise finish.
    @Parameter:
    1. database_name: str = file name for the database.
    @Returns: None.
    """
    with open("{}.csv".format(database_name), "a+"):
        return


def save_db_to_disk(users: dict, database_name: str = default_db_name) -> None:
    """
    Saves the `users` dictionary to the database file `database_name`.csv.
    @Parameter:
    1. users: dict = dictionary of users and their pending messages.
    2. database_name: str = file name for the database.
    @Returns: None.
    """
    with open("{}.csv".format(database_name), "w+") as f:
        db_writer = csv.writer(f)
        for username, messages in list(users.items()):
            db_writer.writerow([username] + messages)

def init_users(database_name: str = default_db_name) -> dict:
    """
    Initializes the `users` dictionary by reading the database file `users.csv`.
    @Parameter:
    1. database_name: str = file name for the database.
    @Returns:
    1. users: dict = dictionary of users and their pending messages.
    @Raises: FileNotFoundError if `users.csv` does not exist.
    """
    users = {}
    with open(f"{database_name}.csv", "r+") as f:
        db_reader = csv.reader(
            f, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True
        )
        for line in db_reader:
            users[line[0]] = line[1:]
    return users