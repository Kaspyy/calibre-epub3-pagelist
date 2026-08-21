"""
Utility functions for the EPUB3 Page List Generator plugin.

Provides icon loading compatible with Calibre's plugin resource system.
"""
from qt.core import QIcon, QPixmap


def get_icons(icon_name, plugin_name='EPUB3 Page List Generator'):
    """
    Load an icon from the plugin's ZIP resources.

    Calibre's plugin loader provides ``get_resources()`` for accessing
    files bundled inside the plugin ZIP archive. This function wraps
    the raw bytes into a QIcon suitable for toolbar buttons.

    :param icon_name: Path within the plugin ZIP (e.g. 'images/icon.png').
    :param plugin_name: Plugin display name.
    :returns: QIcon instance.
    """
    try:
        from calibre.customize.ui import find_plugin
        plugin = find_plugin(plugin_name)
        if plugin is not None:
            resources = plugin.load_resources([icon_name])
            raw = resources.get(icon_name)
            if raw:
                pixmap = QPixmap()
                pixmap.loadFromData(raw)
                return QIcon(pixmap)
    except Exception:
        pass

    # Fallback: return an empty icon (Calibre will show default)
    return QIcon()

