from __future__ import absolute_import, division

import base64
import json
import textwrap


# Templates configuration class
# -----------------------------
import uuid

from plotly import utils
from plotly.io import to_json, to_image
from plotly.offline.offline import _get_jconfig, _plot_html


class RenderersConfig(object):
    """
    Singleton object containing the current renderer configurations
    """
    def __init__(self):
        self._renderers = {}
        self._default = None

    # ### Magic methods ###
    # Make this act as a dict of renderers
    def __len__(self):
        return len(self._renderers)

    def __contains__(self, item):
        return item in self._renderers

    def __iter__(self):
        return iter(self._renderers)

    def __getitem__(self, item):
        renderer = self._renderers[item]
        return renderer

    def __setitem__(self, key, value):
        self._renderers[key] = value

    def __delitem__(self, key):
        # Remove template
        del self._renderers[key]

        # Check if we need to remove it as the default
        if self._default == key:
            self._default = None

    def keys(self):
        return self._renderers.keys()

    def items(self):
        return self._renderers.items()

    def update(self, d={}, **kwargs):
        """
        Update one or more renderers from a dict or from input keyword
        arguments.

        Parameters
        ----------
        d: dict
            Dictionary from renderer names to new renderer objects.

        kwargs
            Named argument value pairs where the name is a renderer name
            and the value is a new renderer object
        """
        for k, v in dict(d, **kwargs).items():
            self[k] = v

    # ### Properties ###
    @property
    def default(self):
        """
        The default renderer, or None if no there is no default

        If not None, the default renderer is automatically used to render
        figures when they are displayed in a jupyter notebook or when using
        the plotly.io.show function

        The names of available templates may be retrieved with:

        >>> import plotly.io as pio
        >>> list(pio.renderers)

        Returns
        -------
        str
        """
        return self._default

    @default.setter
    def default(self, value):

        # TODO: validate coerce value into renderer
        self._default = value

    def __repr__(self):
        return """\
Renderers configuration
-----------------------
    Default renderer: {default}
    Available renderers:
{available}
""".format(default=repr(self.default),
           available=self._available_templates_str())

    def _available_templates_str(self):
        """
        Return nicely wrapped string representation of all
        available template names
        """
        available = '\n'.join(textwrap.wrap(
            repr(list(self)),
            width=79 - 8,
            initial_indent=' ' * 8,
            subsequent_indent=' ' * 9
        ))
        return available


# Make config a singleton object
# ------------------------------
renderers = RenderersConfig()
del RenderersConfig


def to_mimebundle(fig, mime_type, validate=True):
    """
    Convert figure to a mimebundle of the specified bundle type

    Parameters
    ----------
    fig:
        Figure object or dict representing a figure
    mime_type: str
        Bundle type string
    validate: bool (default True)
        True if the figure should be validated before being converted to
        JSON, False otherwise.

    Returns
    -------
    dict
    """
    pass


class MimetypeRenderer(object):

    def to_mimebundle(self, fig_dict):
        raise NotImplementedError()


# JSON
class JsonRenderer(MimetypeRenderer):
    def to_mimebundle(self, fig_dict):
        value = json.loads(to_json(fig_dict))
        return {'application/json': value}


# Plotly mimetype
class PlotlyRenderer(MimetypeRenderer):
    def __init__(self, config=None):
        config = dict(config) if config else {}
        self.config = _get_jconfig(config)

    def to_mimebundle(self, fig_dict):
        if self.config:
            fig_dict['config'] = self.config
        return {'application/vnd.plotly.v1+json': fig_dict}


# Static Image
class ImageRenderer(MimetypeRenderer):
    def __init__(self,
                 mime_type,
                 b64_encode=False,
                 format=None,
                 width=None,
                 height=None,
                 scale=None):

        self.mime_type = mime_type
        self.b64_encode = b64_encode
        self.format = format
        self.width = width
        self.height = height
        self.scale = scale

    def to_mimebundle(self, fig_dict):
        image_bytes = to_image(
            fig_dict,
            format=self.format,
            width=self.width,
            height=self.height,
            scale=self.scale)

        if self.b64_encode:
            image_str = base64.b64encode(image_bytes).decode('utf8')
        else:
            image_str = image_bytes.decode('utf8')

        return {self.mime_type: image_str}


class PngRenderer(ImageRenderer):
    def __init__(self, width=None, height=None, scale=None):
        super(PngRenderer, self).__init__(
            mime_type='image/png',
            b64_encode=True,
            format='png',
            width=width,
            height=height,
            scale=scale)


class SvgRenderer(ImageRenderer):
    def __init__(self, width=None, height=None, scale=None):
        super(SvgRenderer, self).__init__(
            mime_type='image/svg+xml',
            b64_encode=False,
            format='svg',
            width=width,
            height=height,
            scale=scale)


class PdfRenderer(ImageRenderer):
    def __init__(self, width=None, height=None, scale=None):
        super(PdfRenderer, self).__init__(
            mime_type='application/pdf',
            b64_encode=True,
            format='pdf',
            width=width,
            height=height,
            scale=scale)


class JpegRenderer(ImageRenderer):
    def __init__(self, width=None, height=None, scale=None):
        super(JpegRenderer, self).__init__(
            mime_type='image/jpeg',
            b64_encode=True,
            format='jpg',
            width=width,
            height=height,
            scale=scale)


# HTML
class HtmlRenderer(MimetypeRenderer):
    def __init__(self,
                 fullhtml=False,
                 requirejs=True,
                 config=None,
                 auto_play=False):

        config = dict(config) if config else {}
        self.config = _get_jconfig(config)
        self.auto_play = auto_play

    def to_mimebundle(self, fig_dict):
        plotdivid = uuid.uuid4()

        # Serialize figure
        jdata = json.dumps(
            fig_dict.get('data', []), cls=utils.PlotlyJSONEncoder)
        jlayout = json.dumps(
            fig_dict.get('layout', {}), cls=utils.PlotlyJSONEncoder)

        if fig_dict.get('frames', None):
            jframes = json.dumps(
                fig_dict.get('frames', []), cls=utils.PlotlyJSONEncoder)
        else:
            jframes = None

        # Serialize figure config
        config = _get_jconfig(self.config)
        jconfig = json.dumps(config)

        # Platform URL
        plotly_platform_url = config.get('plotly_domain', 'https://plot.ly')

        # Build script body
        if jframes:
            if self.auto_play:
                animate = """.then(function(){{
                    Plotly.animate('{id}');
                }}""".format(id=plotdivid)

            else:
                animate = ''

            script = '''
            if (document.getElementById("{id}")) {{
                Plotly.plot(
                    '{id}',
                    {data},
                    {layout},
                    {config}
                ).then(function () {add_frames}){animate}
            }}
                '''.format(
                id=plotdivid,
                data=jdata,
                layout=jlayout,
                config=jconfig,
                add_frames="{" + "return Plotly.addFrames('{id}',{frames}".format(
                    id=plotdivid, frames=jframes
                ) + ");}",
                animate=animate
            )
        else:
            script = """
        if (document.getElementById("{id}")) {{
            Plotly.newPlot("{id}", {data}, {layout}, {config}); 
        }}
        """.format(
                id=plotdivid,
                data=jdata,
                layout=jlayout,
                config=jconfig)

        # Build div
        plotly_html_div = """
    <div id="{id}" style="class="plotly-graph-div"></div>
    <script type="text/javascript">
        require(["plotly"], function(Plotly) {{
            window.PLOTLYENV=window.PLOTLYENV || {{}};
            window.PLOTLYENV.BASE_URL={plotly_platform_url}
            {script}
        }}
    </script>\n""".format(
            id=plotdivid,
            plotly_platform_url=plotly_platform_url,
            script=script
        )
