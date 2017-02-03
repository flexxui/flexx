# doc-export: VideoViewer
"""
This example demonstrates how static files can be served by making use
of a static file server.

If you intend to create a web application, note that using a static
server is a potential security risk. Use only when needed. Other options
that scale better for large websites are e.g. Nginx, Apache, or 3d party
services like Azure Storage or Amazon S3.

When exported, any links to local files wont work, but the remote links will.
"""

import os

from flexx import app, ui, event

from tornado.web import StaticFileHandler


# The directory to load video's from
dirname = os.path.expanduser('~/Videos')

# Collect videos that look like they can be read in html5
videos = {}
for fname in os.listdir(dirname):
    if fname.endswith('.mp4'):
        videos[fname] = '/videos/' + fname

# Add some online videos too, for fun
videos['bbb.mp4 (online)'] = 'http://www.w3schools.com/tags/mov_bbb.mp4'
videos['ice-age.mp4 (online)'] = ('https://dl.dropboxusercontent.com/u/1463853/'
                                  'ice%20age%204%20trailer.mp4')

# Make use of Tornado's static file handler
tornado_app = app.create_server().app
tornado_app.add_handlers(r".*", [
    (r"/videos/(.*)", StaticFileHandler, {"path": dirname}),
    ])


class VideoViewer(ui.Widget):
    """ A simple videoviewer that displays a list of videos found on the
    server's computer, plus a few online videos. Note that not all videos
    may be playable in HTML5.
    """
    
    def init(self):
        
        with ui.BoxPanel():
            with ui.TreeWidget(max_selected=1, flex=1) as self.videolist:
                for name in sorted(videos):
                    ui.TreeItem(text=name)
            
            self.player = ui.VideoWidget(flex=5)
    
    class JS:
        
        @event.connect('videolist.items*.selected')
        def on_select(self, *events):
            for ev in events:
                if ev.source.selected:
                    fname = ev.source.text
                    self.player.source = videos[fname]


if __name__ == '__main__':
    m = app.launch(VideoViewer)
    app.run()
