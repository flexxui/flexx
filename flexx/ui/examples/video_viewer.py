# doc-export: VideoViewer
"""
This example demonstrates how data can be provided to the client with the
Flexx asset management system. In this case video data.

Other than the serve_data.py example, the data is not loaded in memory,
but linked.

"""

import os

from flexx import app, ui, event


# Dict of names to uri's
videos = {}

# Collect videos 
dirname = os.path.expanduser('~/Videos')
app.assets.add_data_dir(dirname)  # mark this dir as safe to load data from
for fname in os.listdir(dirname):
    if fname.endswith(('.mp4', '.avi')):
        filename = os.path.join(dirname, fname)
        url = app.assets.add_shared_data(fname, 'file://' + filename)
        videos[fname] = url

# Add some online videos too
videos['bbb.mp4 (online)'] = 'http://www.w3schools.com/tags/mov_bbb.mp4'
videos['ice-age.mp4 (online)'] = ('https://dl.dropboxusercontent.com/u/1463853/'
                                  'ice%20age%204%20trailer.mp4')

# Alternatively, remote data can be registed as shared data, in which
# case, the exported app will include the data.
# videos['bbb.mp4 (online)'] = app.assets.add_shared_data('bbb.mp4',
#     'http://www.w3schools.com/tags/mov_bbb.mp4')


class VideoViewer(ui.Widget):
    """ A simple videoviewer that displays a list of videos found on the
    server's computer, plus a few inline videos. Note that not all videos
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
    m = app.launch(VideoViewer, 'firefox')
    app.run()
