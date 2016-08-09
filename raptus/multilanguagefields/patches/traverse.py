# Use those methods to patch traversing methods of content types
# using multilanguage image or file fields

from raptus.multilanguagefields import LOG
from raptus.multilanguagefields.interfaces import IMultilanguageField
from Products.Archetypes.BaseObject import BaseObject

def __bobo_traverse__(self, REQUEST, name):
    """ helper to access multilanguage image scales the old way during
        `unrestrictedTraverse` calls

        the method to be patched is '__bobo_traverse__'
    """
    if name.startswith('image_') or name == 'image':
        field = self.getField(name.split('_')[0])
        if not IMultilanguageField.providedBy(field) or not hasattr(REQUEST, 'get'):
            return BaseObject.__bobo_traverse__(self, REQUEST, name)
        last = REQUEST.get('ACTUAL_URL', '').endswith(name)
        fieldname, scale = name, None
        if '___' in name:
            fieldname, lang, scalename = name.split('___')
            if scalename:
                scale = scalename[1:]
        else:
            if '_' in name:
                fieldname, scale = name.split('_', 1)
            if last and REQUEST.get('HTTP_USER_AGENT', False):
                # begin own code
                if scale in field.getAvailableSizes(self):
                    # end own code
                    _scale = scale
                    if _scale is not None:
                        _scale = '_'+str(_scale)
                    else:
                        _scale = ''
                    REQUEST.RESPONSE.redirect(self.absolute_url()+'/'+fieldname+'___'+field._getCurrentLanguage(self)+'___'+_scale)
            lang = field._getCurrentLanguage(self)
        lang_before = field._v_lang
        try:
            field.setLanguage(lang)
            handler = IImageScaleHandler(field, None)
            image = None
            if handler is not None:
                try:
                    image = handler.getScale(self, scale)
                except AttributeError: # no image available, do not raise as there might be one available as a fallback
                    pass
            if not image: # language fallback
                defaultLang = field.getDefaultLang(self)
                if defaultLang and not defaultLang == lang:
                    field.setLanguage(defaultLang)
                    if handler is not None:
                        image = handler.getScale(self, scale)
                if image is not None:
                    if last and REQUEST.get('HTTP_USER_AGENT', False):
                        _scale = scale
                        if _scale is not None:
                            _scale = '_'+str(_scale)
                        else:
                            _scale = ''
                        REQUEST.RESPONSE.redirect(self.absolute_url()+'/'+fieldname+'___'+defaultLang+'___'+_scale)
        finally:
            field.setLanguage(lang_before)
        if image is not None:
            return image
    return BaseObject.__bobo_traverse__(self, REQUEST, name)

from Products.ATContentTypes.content.image import ATImage
ATImage.__bobo_traverse__ = __bobo_traverse__
LOG.info("Products.ATContentTypes.content.image.ATImage.__bobo_traverse__ patched")
