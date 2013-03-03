

GLOBAL_ID = 10

class User(object):

    def __init__(self, id, user_type):
        self.id = id
        self.user_type = user_type


class UserApi(object):

    resource = {}

    def __init__(self):
        self.resource[1] = User(1, 'admin')
        pass

    def create(self, user_type):
        global GLOBAL_ID
        user = User(GLOBAL_ID, user_type)
        self.resource[user.id] = user
        GLOBAL_ID += 1
        return user

    def delete(self, id):
        del self.resource[id]

    def get(self, id):
        return self.resource[id]


class SpamHttpException(RuntimeError):

    def __init__(self, status_code):
        self.status_code = status_code


class Spam(object):

    def __init__(self, owner_id=None):
        global GLOBAL_ID
        self.owner_id = owner_id
        self.id = GLOBAL_ID
        GLOBAL_ID += 1


class SpamApi(object):

    resources = {}

    def __init__(self, users, user_id):
        self.users = users
        self.user_id = user_id

    def create(self, owner=None):
        if owner:
            user_id = owner
        else:
            user_id = self.user_id
        user_type = self.users.get(user_id).user_type
        if user_type not in ("normal", "admin"):
            raise SpamHttpException(401)
        spam = Spam(owner_id = self.user_id)
        self.resources[spam.id] = spam
        return spam

    def delete(self, id):
        user_type = self.users.get(self.user_id).user_type
        if user_type not in ("normal", "admin"):
            raise SpamHttpException(401)
        del self.resources[id]

    def get(self, id):
        user_type = self.users.get(self.user_id).user_type
        if user_type not in ("normal", "admin", "restricted"):
            raise SpamHttpException(401)
        spam = self.resources[id]
        if spam.id != id:
            raise SpamHttpException(401)
        return spam



class Api(object):

    def __init__(self, user_id):
        self.user_id = user_id
        self.user = UserApi()
        self.spam = SpamApi(self.user, user_id)


def create_admin_api():
    return Api(1)

def create_api(user_id):
    return Api(user_id)
