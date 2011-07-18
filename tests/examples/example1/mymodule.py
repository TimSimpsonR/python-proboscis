
database = None
web_server = None

def create_database():
    global database
    database = {}

def destroy_database():
    global database
    database = None

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


def stop_web_server():
    global web_server
    web_server = None


def tables_exist():
    return database != None


class ServiceClient(object):

    ADMIN = "admin"
    NOBODY = "nobody"

    def __init__(self, settings):
        self.user_name = settings["user_name"]

    @property
    def check_credentials(self):
        return web_server[self.user_name]["credentials"]

    def get_profile_image(self):
        return web_server[self.user_name]["image"]

    def set_profile_image(self, new_value):
        web_server[self.user_name]["image"] = new_value

    def service_is_up(self):
        return web_server != None