from flask import Flask, current_app, url_for
from flask_sockets import Sockets
app = Flask(__name__)

from flexx import ui, flx, flx_flask


######################## The flexx application #########################
class Example(flx.Widget):

    def init(self):
        content = "# Welcome\n\n" \
            "This flexx app is served within flask! "
        ui.Markdown(content=content, style='background:#EAECFF;')

flx_flask.serve(Example)

@app.route("/")
def site_map():  # list available applications and URLs
    """
    This function lists all the URLs server by the flask application
    including the flexx application that have been registered.
    """
    def has_no_empty_params(rule):
        defaults = rule.defaults if rule.defaults is not None else ()
        arguments = rule.arguments if rule.arguments is not None else ()
        return len(defaults) >= len(arguments)
    links = []
    for rule in current_app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append((url, rule.endpoint))
    # links is now a list of url, endpoint tuples
    html = ["<h> URLs served by this server </h>", "<ul>"]
    for link in links:
        html.append(f'<li><a href="{link[0]}">{link[1]}</a></li>')
    html.append("</ul>")
    return '\n'.join(html)

####################### Registration of blueprints #####################
sockets = Sockets(app)  # keep at the end
flx_flask.register_blueprints(app, sockets)

####################### Start flexx in thread #####################
import threading
import asyncio
def flexx_thread():
    """
    Function to start a thread containing the main loop of flexx.
    This is needed as flexx is an asyncio application which is not 
    compatible with flexx/gevent.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    flx_flask.start() # starts flexx loop without server
thread1 = threading.Thread(target = flexx_thread)
thread1.daemon = True
thread1.start()

######### Start flask server (using gevent that supports web sockets) #########
if __name__ == "__main__":

    @app.errorhandler(Exception)
    def internal_error(e):
        import traceback; traceback.print_exc()  # get the trace stack
        err_str = str(traceback.format_exc())  # to get the string
        err_str = err_str.replace("\n", "<br>")
        return "<h3>" + str(e) + "</h3><br>" + err_str

    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    def RunServer():
        server = pywsgi.WSGIServer(('127.0.0.1', 5000), app, handler_class=WebSocketHandler)
        print("Server Started!")
        server.serve_forever()

    RunServer()
