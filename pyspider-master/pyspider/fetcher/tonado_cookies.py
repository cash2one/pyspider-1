import requests.cookies
import Cookie

def cookie_to_dict(cookie):
    """Convert a string cookie into a dict"""
    cookie_dict = dict()
    C = Cookie.SimpleCookie(cookie)
    for morsel in C.values():
        cookie_dict[morsel.key] = morsel.value
    return cookie_dict

def dict_to_cookie(cookie_dict):
    attrs = []
    for (key, value) in cookie_dict.items():
        attrs.append("%s=%s" % (key, value))
    return "; ".join(attrs)

def get_cookie(request, response):
    """Returns cookie string by tonado AsyncHTTPClient's request and response
    :param request: class:tornado.httpclient.HTTPRequest
    :param response: class:tornado.httpclient.HTTPResponse
    """
    cookiejar = requests.cookies.RequestsCookieJar()

    if request and request.headers.get("Cookie"):
        request_cookie = request.headers.get("Cookie")
        if type("") != type(request_cookie):
            request_cookie = request_cookie.encode("utf-8")
        cookie_dict = cookie_to_dict(request_cookie)
        requests.cookies.cookiejar_from_dict(cookie_dict, cookiejar)

    for sc in response.headers.get_list("Set-Cookie"):
        C = Cookie.SimpleCookie(sc)
        for morsel in C.values():
            cookie = requests.cookies.morsel_to_cookie(morsel)
            cookiejar.set_cookie(cookie)
    cookie_dict = cookiejar.get_dict(path="/")
    return dict_to_cookie(cookie_dict)

if __name__ == '__main__':
    cookie_str = 'CXID=A007539E666312CD09DDFBADAD4228BC; SUID=64A66A717A1C900A55CBFA3600021C52; SUV=1440126715355038; IPLOC=CN4403; ssuid=4336904316; _ga=GA1.2.1595243810.1441980481; ad=HZllllllll2qh@oLlllllVB@Y79llllltQ$uBlllll9lllllpCxlw@@@@@@@@@@@; ABTEST=0|1451363637|v1; weixinIndexVisited=1; SNUID=FB68B7774C49644F02E4EEA24D5FD1FA; sct=10; LSTMV=29%2C311; LCLKINT=1214'
    print cookie_to_dict(cookie_str)