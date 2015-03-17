import websocket
import _thread
import time
import http.client as httplib
import sys
import saltwatch as sw

last_time = time.clock()
TIMER_RESET = 1.

def on_message(ws, message):
    global last_time 

    print(message)
    if message == u'2::':
        ws.send(message)
    if message == u'3::':
        if time.time() - last_time > TIMER_RESET:
            last_time = time.clock()
            state = sw.get_state()
            sw.process_state(state)
            #print(state_json)


def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")
    sw.save_persistent_data()

def on_open(ws):
    """    def run(*args):
        for i in range(3):
            time.sleep(1)
            ws.send("Hello %d" % i)
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    _thread.start_new_thread(run, ())
    """
    return    


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
    sw.load_persistent_data()

    websocket.enableTrace(True)
    
    ws = connect('www-cdn-twitch.saltybet.com', 8000)

    ws.run_forever()
