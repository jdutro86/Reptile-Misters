import hashlib
import os

class User(object):
    
    '''
    Initializes a User with a name and password. The salt is a key
    to store a hashed password, and the hashed password is stored in key.
    '''
    def __init__(self, name, password):
        self.name = name
        self.salt = os.urandom(32)
        self.key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), self.salt, 100000)
        
    def get_name(self):
        self.name
        
    def get_salt(self):
        return self.salt
    
    def get_key(self):
        return self.key

class UserList(list):
    
    '''
    Initializes a list of User objects 
    '''
    def __init__(self):
        self.users = [0]
        
    def add_user(self, name, password):
        self.users.append(User(name,password))
        
    def delete_user(self, name):
        if name in self.users.get_name():
            users.remove(name)
            
    def check_password(self, password):
        hashedpass = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), self.salt, 100000)
        if hashedpass in self.users.get_key():
            return self.users.get_name()