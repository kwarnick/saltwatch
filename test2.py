import websocket, sys, asyncore
import http.client as httplib


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
        
        
def on_open(ws):
    print("opened!")
 
 
def on_message(ws, msg):
    print("msg: " + str(msg))
 
 
def on_close(ws):
    print("closed!")
 
 
if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.stderr.write('usage: python client.py <server> <port>\n')
        sys.exit(1)
    
    server = sys.argv[1]
    port = int(sys.argv[2])
    
    ws = connect(server, port)

    ws.run_forever()
    #try:
    #    asyncore.loop()
    #except KeyboardInterrupt:
    #    ws.close()
