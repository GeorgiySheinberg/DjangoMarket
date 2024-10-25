import requests

url = 'http://127.0.0.1:8000/update/'

fp = open('shop1.yaml', 'rb')
file = {'file': fp}
token = "730093332e54b20878dd389cd08dc6020d1b695a"


response = requests.post(url, headers={"Authorization": f'Token {token}'}, files=file)
print(response.text)
print(response.status_code)

# response = requests.post(url="http://127.0.0.1:8000/auth/token/login/",
#                          data={
#                              "email": "georgiysheinberg@gmail.com",
#                              "password": "jocker12345"
#                          })
# print(response.status_code)
# print(response.text)