from flexx import app, ui, event


class Authentication(ui.Widget):
    
    def init(self):
        
        self.edit = ui.LineEdit(placeholder_text='username',
                                text=self.session.get_cookie('username', ''))
        
    @event.connect('edit.text')
    def _update_cookie(self, *events):
        self.session.set_cookie('username', self.edit.text)

##


import os

# Dict that google gave me
info2 = {"client_id":"515650829929-ilthmjde5nkccn1saa0mt06b69tc5gdl.apps.googleusercontent.com",
         "client_secret":"jQZvHZFQByvIIHVjSTRhAH1k",
         "project_id" :"flexx-1284",
         "auth_uri":"https://accounts.google.com/o/oauth2/auth",
         "token_uri":"https://accounts.google.com/o/oauth2/token",
         "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
         "redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]
         }

# This is the public key by which this app is registered, this may be in source
info2['key'] = info2['client_id']
# This is the secret key by which this "app" is registered, should not be in source
info2['secret'] = info2['client_secret']
# For tornado to store its cookies in a good way, should not be in source
info2['cookie_secret'] = "32oETzKXQAFlexx5gEmGeJJFuYh7EQnp2XdTP1oVo"

info2['userinfo_uri'] = "https://www.googleapis.com/oauth2/v1/userinfo"

import logging
import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.web



class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        # todo: store on session, not on application! or on cookie
        return getattr(self.application, '_the_user_info', None)
        #return self.get_secure_cookie_dict("user")
    
    def get_secure_cookie_dict(self, name):
        cookie = self.get_secure_cookie(name)
        if cookie:
            return tornado.escape.json_decode(cookie)
     
    def set_secure_cookie_dict(self, name, cookie):
        if not isinstance(cookie, dict):
            raise ValueError('Cookie should be a dict')
        self.set_secure_cookie(name, tornado.escape.json_encode(cookie))


class MainHandler(BaseHandler):
    
    @tornado.web.authenticated  # this forces that user is logged in, redirects to login_url if not
    def get(self):
        user = self.current_user
        name = tornado.escape.xhtml_escape(user["name"])
        self.write('Hello, %s <img src="%s" />' % (name, user['picture']))

## We can provide a few common cases, users can provide one too

# Define Mixin classes that can provide 
from tornado.auth import urllib_parse, urlparse, functools, AuthError, escape

class GoogleOAuth2Mixin(tornado.auth.OAuth2Mixin):
    """Google authentication using OAuth2.
    """
    _OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/auth"
    _OAUTH_ACCESS_TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
    _OAUTH_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"
    _OAUTH_NO_CALLBACKS = False
    _OAUTH_SETTINGS_KEY = 'google_oauth'

    @tornado.auth._auth_return_future
    def get_authenticated_user(self, redirect_uri, code, callback):
        http = self.get_auth_http_client()
        body = urllib_parse.urlencode({
            "redirect_uri": redirect_uri,
            "code": code,
            "client_id": self.settings[self._OAUTH_SETTINGS_KEY]['key'],
            "client_secret": self.settings[self._OAUTH_SETTINGS_KEY]['secret'],
            "grant_type": "authorization_code",
        })

        http.fetch(self._OAUTH_ACCESS_TOKEN_URL,
                   functools.partial(self._on_access_token, callback),
                   method="POST", headers={'Content-Type': 'application/x-www-form-urlencoded'}, body=body)

    def _on_access_token(self, future, response):
        """Callback function for the exchange to the access token."""
        if response.error:
            future.set_exception(AuthError('Google auth error: %s' % str(response)))
            return

        args = escape.json_decode(response.body)
        future.set_result(args)
    
    @tornado.gen.coroutine
    def get_user(self, access_token=None):
        """ Gives pictire, id, locale, gender, name, link, family_name, given_name.
        """
        user = yield self.oauth2_request(self._OAUTH_USERINFO_URL, access_token=access_token)
        return user
    
    @tornado.gen.coroutine
    def redirect_for_user_info(self, redirect_uri):
        # scope: profile, email
        yield self.authorize_redirect(
            redirect_uri=redirect_uri,
            client_id=self.settings[self._OAUTH_SETTINGS_KEY]['key'],
            scope=['profile'],  # add email etc. here
            response_type='code',
            extra_params={'approval_prompt': 'auto'})


tornado.httpclient.AsyncHTTPClient.configure(
    None, defaults=dict(user_agent="Flexx"))


class BaseAuthHandler(BaseHandler):
    
    def __init__(self, *args):
        super().__init__(*args)
        # self._OAUTH_AUTHORIZE_URL = info2['auth_uri']
        # self._OAUTH_ACCESS_TOKEN_URL = info2['token_uri']
        # self._OAUTH_USERINFO_URL = info2['userinfo_uri']
        # self._OAUTH_NO_CALLBACKS = False
    
    @tornado.gen.coroutine
    def get(self, path):
        """ The steps below are generally performed in bottom-to top order,
        but sometimes only the top (few) are needed, e.g. we already have
        an access token, and only need the corresponding user name.
        """
        url = self.request.full_url().split('?')[0]
        print('auth handler GET at ', url)
        if url.endswith('/new'):
            self.clear_cookie("user")
            self.clear_cookie("access")
            self.application._the_user_info = None
            self.redirect(url.rsplit('/', 1)[0])
        elif self.get_current_user():
            # We have a user, no need to login
            print('logged in ..', self.get_current_user())
            self.redirect('/')
        elif self.get_secure_cookie_dict("access"):
            # We have access, but no user yet
            access = self.get_secure_cookie_dict("access")
            print('get user info ..')
            try:
                user = yield self.get_user(access_token=access["access_token"])
            except tornado.auth.AuthError:
                raise
                logging.warn('Failed to get user info via OAuth, re-authenticating...')
                self.clear_cookie('access')
                self.redirect(url)
                # todo: this is where we could try use the refresh token
                return
            #application.user = user
            # todo: verify user, check email? google does not give username
            #self.set_secure_cookie_dict("user", user)
            self.application._the_user_info = user
            self.redirect(url)
        elif self.get_argument('code', False):
            # We get here once the authorize_redirect() has succeeded
            print('get authenticated user ..')
            access = yield self.get_authenticated_user(
                redirect_uri=url,
                code = self.get_argument('code'))
            self.set_secure_cookie_dict("access", access)
            self.redirect(url)
        else:
            # We start from scratch, ask OAuth provider for a token
            print('authorize redirect ..')
            yield self.redirect_for_user_info(url)


application = tornado.web.Application([
            (r"/", MainHandler),
            ],#(r"/login", GoogleAuthHandler)],
            login_url="/login",
        )


# To handle in script file

class GoogleAuthHandler(BaseAuthHandler, GoogleOAuth2Mixin):
    pass

server = app.create_server()

#application.settings['app_name'] = 'flexxample'
server.app.settings['cookie_secret'] = info2['cookie_secret']
server.app.settings['google_oauth'] = info2

server.app.add_handlers(".*$", [(r"/login/?(.*)", GoogleAuthHandler)])


m = app.launch(Authentication, 'browser')
