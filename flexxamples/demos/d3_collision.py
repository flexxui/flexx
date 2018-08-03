# doc-export: CollisionWidget
"""
Example using 3D. Adapted from a demo by Mike Bostock.
"""

from flexx import flx
from pscript import RawJS
from pscript.stubs import Math, d3, window

flx.assets.associate_asset(__name__, 'https://d3js.org/d3.v3.min.js')


class CollisionWidget(flx.Widget):
    """ A widget showing a collision demo based on D3.
    """

    CSS = """
    .flx-CollisionWidget {
        background: #fff;
        border: 1px solid black;
        border-radius: 6px;
    }
    """

    def init(self):
        self.node.id = self.id
        window.setTimeout(self.load_viz, 500)

    @flx.reaction
    def _resize(self):
        w, h = self.size
        if len(self.node.children) > 0:
            svg = self.node.children[0]
            svg.setAttribute('width', w)
            svg.setAttribute('height', h)

    def load_viz(self):

        w, h = self.size

        nodes = d3.range(200).map(lambda: {'radius': Math.random() * 12 + 4})
        color = d3.scale.category10()

        force = d3.layout.force().gravity(0.05).charge(lambda d, i: 0 if i else -2000)\
            .nodes(nodes).size([w, h])

        root = nodes[0]
        root.radius = 0
        root.fixed = True

        force.start()

        x = d3.select('#' + self.id)
        print(x, self.id)
        svg = RawJS('x.append("svg").attr("width", w).attr("height", h)')

        x = RawJS(
            'svg.selectAll("circle").data(nodes.slice(1)).enter().append("circle")')
        x.attr("r", lambda d: d.radius).style("fill", lambda d, i: color(i % 3))

        def on_tick(e):
            q = d3.geom.quadtree(nodes)
            i = 0
            n = nodes.length
            while i < n-1:
                i += 1
                q.visit(collide(nodes[i]))
            svg.selectAll("circle").attr("cx", lambda d: d.x).attr("cy", lambda d: d.y)

        force.on("tick", on_tick)

        def on_mousemove():
            p1 = d3.mouse(self.node)
            root.px = p1[0]
            root.py = p1[1]
            force.resume()

        svg.on("mousemove", on_mousemove)

        def collide(node):
            r = node.radius + 16
            nx1 = node.x - r
            nx2 = node.x + r
            ny1 = node.y - r
            ny2 = node.y + r

            def func(quad, x1, y1, x2, y2):
                if quad.point and quad.point is not node:
                    x = node.x - quad.point.x
                    y = node.y - quad.point.y
                    s = Math.sqrt(x * x + y * y)
                    r = node.radius + quad.point.radius
                    if (s < r):
                        s = (s - r) / s * .5
                        x *= s
                        y *= s
                        node.x -= x
                        node.y -= y
                        quad.point.x += x
                        quad.point.y += y
                return x1 > nx2 or x2 < nx1 or y1 > ny2 or y2 < ny1
            return func


class CollisionDemo(flx.Widget):

    def init(self):
        with flx.VSplit():
            with flx.HSplit():
                CollisionWidget()
                CollisionWidget()
            with flx.HSplit():
                CollisionWidget()
                CollisionWidget()


if __name__ == '__main__':
    flx.launch(CollisionDemo, 'app')
    flx.run()
