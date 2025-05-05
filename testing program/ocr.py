import requests

api_token = 'Token YOUR_API'
image_path = r'C:\Users\CHU\Desktop\vision\image.jpg'

with open(image_path, 'rb') as fp:
    response = requests.post(
        'https://api.platerecognizer.com/v1/plate-reader/',
        headers={'Authorization': api_token},
        files={'upload': fp}
    )

print(response.status_code)
print(response.json())
