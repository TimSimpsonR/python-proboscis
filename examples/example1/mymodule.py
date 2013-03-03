import random

database = None
web_server = None

class AuthException(Exception):
    pass

class UserNotFoundException(Exception):
    pass


def create_database():
    global database
    database = { 'users':{} }

def destroy_database():
    global database
    database = None


def get_admin_client():
    return UserServiceClient(0, { 'username':"admin", 'password':None })

def login(user_settings):
    for user in database['users'].values():
        if user.username == user_settings['username']:
            if user.password != user_settings['password']:
                raise UserNotFoundException()
            else:
                return user
    raise UserNotFoundException()

def reverse(string):
    """Reverses a string."""
    return string[::-1]

def start_web_server():
    global web_server
    web_server = {
        "bob": {
            "credentials":"admin",
            "image":"default.jpg"
        }
    }


def bad_start_web_server():
    raise RuntimeError("Error starting service.")


def stop_web_server():
    global web_server
    web_server = None


def tables_exist():
    return database != None


class UserServiceClient(object):

    def __init__(self, id, settings):
        self.id = id
        self.username = settings['username']
        self.password = settings['password']
        self.type = settings.get('type', 'normal')

    @property
    def check_credentials(self):
        return web_server[self.username]["credentials"]

    def create_user(self, settings):
        if self.id != 0 and self.type != 'admin':
            raise AuthException("Must be an Admin to perform this function.")
        random.seed()
        id = random.randint(1, 1000)
        settings['id'] = id
        user = UserServiceClient(id, settings)
        database['users'][id] = user
        web_server[user.username] = {'image':"default.jpg"}
        return user

    def delete_user(self, id):
        if self.id != 0 and self.type != 'admin':
           raise AuthException("Must be an Admin to perform this function.")
        if id not in database['users']:
            raise UserNotFoundException()
        del database['users'][id]


    def get_profile_image(self):
        return web_server[self.username]["image"]

    def set_profile_image(self, new_value):
        web_server[self.username]["image"] = new_value

    def service_is_up(self):
        return web_server != None
