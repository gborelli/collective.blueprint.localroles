from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
# from collective.transmogrifier.utils import Condition
from collective.transmogrifier.utils import defaultMatcher

from Acquisition import aq_base
# from Products.CMFCore.utils import getToolByName

import logging
logger = logging.getLogger('collective.blueprint.localroles')


class setLocalRoles(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context
        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            keys = item.keys()
            pathkey = self.pathkey(*keys)[0]

            if not pathkey:
                yield item; continue
            path = item[pathkey]

            path = path.encode('ASCII')
            elems = path.strip('/').rsplit('/', 1)
            container, id = (len(elems) == 1 and ('', elems[0]) or elems)
            context = self.context.unrestrictedTraverse(container, None)
            if context is None:                       # container doesn't exist
                error = 'Container %s does not exist for item %s' % (container, path)
                logger.warn(error)
                yield item; continue

            obj = getattr(aq_base(context), id, None)
            if obj is None: # item not exists
                yield item; continue

            if not item.get('localroles', None):
                yield item; continue

            try:
                # item['localroles'] = [{'username': 'user_1', 
                #                        'roles': ('role_1','role_2')},
                #                       {'username': 'user_2', 
                #                        'roles': ('role_x')}]
                for user_roles in item['localroles']:
                    obj.manage_setLocalRoles(user_roles[0], user_roles[1])
            except:
                logger.warn("Can't set the local roles on item %s" % path)

            yield item


class getLocalRoles(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.root = transmogrifier.context.unrestrictedTraverse(options.get('source_root', None))
        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            keys = item.keys()
            pathkey = self.pathkey(*keys)[0]

            if not pathkey:
                yield item; continue
            path = item[pathkey]

            path = path.encode('ASCII')
            elems = path.strip('/').rsplit('/', 1)
            container, id = (len(elems) == 1 and ('', elems[0]) or elems)
            context = self.root.unrestrictedTraverse(container, None)
            if context is None:                       # container doesn't exist
                error = 'Container %s does not exist for item %s' % (container, path)
                logger.warn(error)
                yield item; continue

            obj = getattr(aq_base(context), id, None)
            if obj is None and context.getId() != item.get('id', None): # item not exists
                yield item; continue

            # the first element of chain is the root of chain (?)
            if context.getId() == item.get('id', None):
                obj = context

            try:
                item['localroles'] = obj.get_local_roles()
            except:
                pass

            yield item