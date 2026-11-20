import requests

BASE_URL = "http://127.0.0.1:5000"
TIMEOUT = 5


class ServerNedostupen(Exception):
    pass


def _zapros(method, path, **kwargs):
    kwargs.setdefault("timeout", TIMEOUT)
    url = BASE_URL + path
    try:
        r = requests.request(method, url, **kwargs)
    except (requests.ConnectionError, requests.Timeout) as e:
        raise ServerNedostupen(f"не удалось связаться с сервером: {e}")

    if r.status_code >= 500:
        raise ServerNedostupen(f"сервер вернул ошибку {r.status_code}")

    return r


def poluchit_vse_ankety():
    r = _zapros("GET", "/anketi")
    return r.json()


def poluchit_anketu(nomer):
    r = _zapros("GET", f"/anketi/{nomer}")
    if r.status_code == 404:
        return None
    return r.json()


def proverka_pochty(mail):
    r = _zapros("POST", "/proverka", json={"mail": mail})
    data = r.json()
    return data.get("prinyato", data.get("prinyato "))


def poluchit_statistiku():
    r = _zapros("GET", "/statistika")
    return r.json()
