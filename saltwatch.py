import websocket
import time
import sys
try:
    import httplib
except ImportError:
    import http.client as httplib 
import saltfetch as sf

# Global variables/params for timed behaviors
last_state_check = time.time()
last_data_write = time.time()
STATE_CHECK_COOLDOWN = 2.    # Don't get state twice in a cooldown period - prevent duplicates
DATA_WRITE_PERIOD = 1*60*60  # Save data to disk evey hour


def on_message(ws, message):
    print(message)
    global last_state_check, last_data_write
    
    # Check if we're due to save data to disk
    if time.time() - last_data_write > DATA_WRITE_PERIOD:
        sf.save_persistent_data()
        last_data_write = time.time()
    
    # Echo keepalive message
    if message == u'2::':
        ws.send(message)
    # Handle state change notifications, which sometimes come in redundant pairs
    if message == u'3::':
        if time.time() - last_state_check > STATE_CHECK_COOLDOWN:
            state = sf.get_state()
            last_state_check = time.time()
            print(state)
            sf.process_state(state)


def on_error(ws, error):
    print(error)


def on_close(ws):
    sf.save_persistent_data()
    print("### closed ###")


def on_open(ws):
    print("### open ###")


def connect(server, port):
    print("connecting to: %s:%d" %(server, port))

    conn  = httplib.HTTPConnection(server + ":" + str(port))
    conn.request('POST','/socket.io/1/')
    resp  = conn.getresponse()
    hskey = resp.read().decode('utf-8').split(':')[0]

    ws = websocket.WebSocketApp(
                    'ws://'+server+':'+str(port)+'/socket.io/1/websocket/'+hskey,
                    on_open   = on_open,
                    on_message = on_message,
                    on_close = on_close)
    
    return ws


if __name__ == "__main__":
    sf.load_persistent_data()

    websocket.enableTrace(True)
    ws = connect('www-cdn-twitch.saltybet.com', 8000)
    ws.run_forever()
