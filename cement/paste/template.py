"""Definition for Cement laycement templates."""

from paste.script import templates
from tempita import paste_script_template_renderer

class CementAppTemplate(templates.Template):
    """
    Cement default paste template class
    """
    _template_dir = 'templates/cementapp'
    template_renderer = staticmethod(paste_script_template_renderer)
    summary = 'Cement Standard Template'
    egg_plugins = ['PasteScript', 'Cement']
    vars = []

    def pre(self, command, output_dir, vars):
        """Called before template is applied."""
        pass

class CementPluginTemplate(templates.Template):
    """
    Cement plugin default paste template class.
    """
    _template_dir = 'templates/cementplugin'
    template_renderer = staticmethod(paste_script_template_renderer)
    summary = 'Cement Plugin Standard Template'
    egg_plugins = ['PasteScript', 'Cement']
    vars = [
        templates.var("plugin", "cement plugin name", default=None),
        templates.var("project", "Parent application this plugin is for", default=None)
        ]

    def pre(self, command, output_dir, vars):
        """Called before template is applied."""
        pass