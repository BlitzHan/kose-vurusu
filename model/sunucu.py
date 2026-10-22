"""Yerel sunucu: siteyi sunar, tarayıcıdaki toplayıcıdan gelen ham veriyi ham/ altına yazar.

Kullanım: python3 model/sunucu.py [port]   (repo kökünden)
POST /ham/<ad>.json  → ham/<ad>.json
"""
import http.server, os, re, sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAM = os.path.join(KOK, 'ham')


class Isleyici(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=KOK, **k)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        m = re.fullmatch(r'/ham/([\w.-]+\.json)', self.path)
        if not m:
            self.send_error(404)
            return
        govde = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        os.makedirs(HAM, exist_ok=True)
        with open(os.path.join(HAM, m.group(1)), 'wb') as f:
            f.write(govde)
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(f'kaydedildi {len(govde)} bayt'.encode())


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8643
    http.server.ThreadingHTTPServer(('127.0.0.1', port), Isleyici).serve_forever()
