import websocket, sys, asyncore
import http.client as httplib


def connect(server, port):
   
    print("connecting to: %s:%d" %(server, port))
    
    conn  = httplib.HTTPConnection(server + ":" + str(port))
    conn.request('POST','/socket.io/1/')
    resp  = conn.getresponse() 
    hskey = resp.read().decode('utf-8').split(':')[0]
 
    ws = websocket.WebSocket(
                    'ws://'+server+':'+str(port)+'/socket.io/1/websocket/'+hskey,
                    onopen   = _onopen,
                    onmessage = _onmessage,
                    onclose = _onclose)
    
    return ws
        
        
def _onopen():
    print("opened!")
 
 
def _onmessage(msg):
    print("msg: " + str(msg))
 
 
def _onclose():
    print("closed!")
 
 
if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.stderr.write('usage: python client.py <server> <port>\n')
        sys.exit(1)
    
    server = sys.argv[1]
    port = int(sys.argv[2])
    
    ws = connect(server, port)
    
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        ws.close()
