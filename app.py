
from tools import app
import eventlet.wsgi

port = 9000
if __name__ == '__main__':
    # app.run(port=port, host="0.0.0.0",debug=True)
    eventlet.wsgi.server(eventlet.listen(("", port)), app)