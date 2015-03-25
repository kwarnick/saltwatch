import websocket
from time import time, sleep
import sys
try:
    import httplib
except ImportError:
    import http.client as httplib 
import saltprocessing as sp
import saltstorage as ss
import saltbettor as sb


# Global variables/params for timed behaviors
STATE_CHECK_COOLDOWN = 2.    # Don't get state twice in a cooldown period - prevent duplicates
DATA_WRITE_PERIOD = 1*60*60  # Save data to disk every hour
MODEL_RELOAD_PERIOD = 1*60*60   # Reload the model from disk every hour
CONNECTION_RETRY_COOLDOWN = 30  # If connection fails, try to reconnect after a cooldown
last_state_check = 0 # Start with no cooldown
last_data_write = 0
last_model_load = 0


def on_message(ws, message):
    print(message)
    global last_state_check, last_data_write, last_model_load
    
    # Check if we're due to save data to disk
    if time() - last_data_write > DATA_WRITE_PERIOD:
        ss.save_persistent_data()
        last_data_write = time()

    # Check if we're due to reload the model
    if time() - last_model_load > MODEL_RELOAD_PERIOD:
        ss.load_model()
        last_model_load = time()
    
    # Echo keepalive message
    if message == u'2::':
        ws.send(message)
    # Handle state change notifications, which sometimes come in redundant pairs
    if message == u'3::':
        if time() - last_state_check > STATE_CHECK_COOLDOWN:
            state = sp.get_state()
            last_state_check = time()
            print(state)
            mode, status, match = sp.process_state(state)  

            # Explicitly have saltstorage and saltbettor react to the update
            ss.act_on_processed_state(mode, status, match)
            sb.act_on_processed_state(mode, status, match)


def on_error(ws, error):
    print(error)


def on_close(ws):
    ss.save_persistent_data()
    print("### closed ###")

    while True:
        # Retry connection after cooldown period
        print('Waiting {:d}s to reconnect'.format(CONNECTION_RETRY_COOLDOWN))
        # Attempt reconnect
        sleep(CONNECTION_RETRY_COOLDOWN)  
        try:
            websocket.enableTrace(True)
            ws = connect('www-cdn-twitch.saltybet.com', 8000)
            ws.run_forever()
        except: 
            continue
        break



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
    ss.load_persistent_data()
    ss.load_model()
    sb.login()

    websocket.enableTrace(True)
    ws = connect('www-cdn-twitch.saltybet.com', 8000)
    ws.run_forever()
