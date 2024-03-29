# django
from django import forms

# third party
from mapwidgets.settings import mw_settings
from mapwidgets.widgets import minify_if_not_debug
from mapwidgets import GooglePointFieldWidget


class CustomGooglePointFieldWidget(GooglePointFieldWidget):
    @property
    def media(self):
        css = {
            "all": [
                minify_if_not_debug("mapwidgets/css/map_widgets{}.css"),
            ]
        }

        js = []

        if not mw_settings.MINIFED:  # pragma: no cover
            js = js + [
                "mapwidgets/js/jquery_class.js",
                "mapwidgets/js/django_mw_base.js",
                "mapwidgets/js/mw_google_point_field.js",
            ]
        else:
            js = js + [
                "mapwidgets/js/mw_google_point_field.min.js"
            ]

        return forms.Media(js=js, css=css)