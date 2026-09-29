import requests
from config import BASE_URL, HEADERS


def test_github_api():
    url = f"{BASE_URL}/user"

    response = requests.get(
        url,
        headers=HEADERS
    )

    print("Status Code:", response.status_code)

    if response.status_code == 200:
        data = response.json()

        print("Authentication successful!")
        print("GitHub Username:", data["login"])

    else:
        print("Authentication failed.")
        print(response.text)


if __name__ == "__main__":
    test_github_api()
