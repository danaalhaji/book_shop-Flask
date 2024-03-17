import unittest
import requests


class TestAPI(unittest.TestCase):
    URL = "http://127.0.0.1:5000"
    URL_LOGIN = "http://127.0.0.1:5000/login"
    URL_REG = "http://127.0.0.1:5000/register"

    data_login = {
        "email" : "test",
        "password" :"password test"
    }

    data_register = {
        "name" : "name",
        "email" : "test",
        "password" :"password test",
        "confirm_password" :"password test"
    }

    def test_home_page(self):
        resp = requests.get(self.URL)
        self.assertEqual(resp.status_code , 200)
        print("Success for Home Page")


    def test_login(self):
        resp = requests.POST(self.URL_LOGIN , json=self.data_login)
        self.assertEqual(resp.status_code , 200)
        print("Success for login")
    
    
    def test_reg(self):
        resp = requests.POST(self.URL_REG , json=self.data_register)
        self.assertEqual(resp.status_code , 200)
        print("Success for login")