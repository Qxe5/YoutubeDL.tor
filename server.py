import os
import http.server
import urllib.parse

import youtube_dl

class HTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def backlink(self, msg):
        return b'<p>%b</p><a href="/">Return Home</a>' % msg

    def forbidmsg(self):
        self.send_response(403)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()

        self.send(self.backlink(b'Not Allowed'))

    def send(self, resp):
        try:
            self.wfile.write(resp)
        except (BrokenPipeError, ConnectionResetError):
            self.wfile.flush()

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            with open('index.html', 'rb') as index:
                self.send(index.read())
        elif self.path == '/favicon.ico':
            self.send_response(200)
            self.send_header('Content-Type', 'image/x-icon')
            self.end_headers()

            with open('favicon.ico', 'rb') as icon:
                self.send(icon.read())
        elif self.path.startswith('/dl?url='):
            url = urllib.parse.unquote(self.path.partition('=')[2])

            dler = youtube_dl.YoutubeDL({'proxy' : 'socks5://127.0.0.1:9050', 'format' : 'mp4'})
            vid_info = None
            try:
                vid_info = dler.extract_info(url)
            except youtube_dl.utils.DownloadError:
                self.send_response(400)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()

                self.send(self.backlink(b'Invalid URL'))

                self.close_connection = True
                return

            filename = vid_info.get('title') + '-' + vid_info.get('id') + '.mp4'

            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            with open('video.html', 'rb') as video_html:
                try:
                    self.wfile.write(video_html.read().replace(b'%FILENAME', filename.encode()))
                except (BrokenPipeError, ConnectionResetError):
                    self.wfile.flush()
                    os.unlink(filename)
        elif self.path.endswith('.mp4'):
            filename = urllib.parse.unquote(self.path)[1:]

            if (os.path.exists(filename)):
                self.send_response(200)
                self.send_header('Content-Type', 'video/mp4')
                self.end_headers()

                with open(filename, 'rb') as video:
                    self.send(video.read())

                os.unlink(filename)
            else:
                self.forbidmsg()
        else:
            self.forbidmsg()

        self.close_connection = True

with http.server.ThreadingHTTPServer(('127.0.0.1', 8080), HTTPRequestHandler) as server:
    server.serve_forever()
