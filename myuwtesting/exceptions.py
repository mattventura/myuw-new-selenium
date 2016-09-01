#!/usr/bin/python

from functions import getCardName


class MyuwDateTypeError(TypeError):
    '''Pre-packaged exception for when an invalid date format is
    specified when constructing a myuwDate. '''
    def __init__(self, *args):
        args = repr(args)
        message = ('Arguments to myuwDate must be "yyyy-mm-dd", got %s '
                   'instead' % args)
        super(MyuwDateTypeError, self).__init__(message)


class LandingWaitTimedOut(Exception):
    def __init__(self, els):
        cardNames = []
        for el in els:
            cardName = getCardName(el)
            cardNames.append(cardName)
        self.cardsNotLoaded = cardNames
        super(LandingWaitTimedOut, self).__init__(
            'Waited too long for landing page to finish loading. The '
            'following cards did not load: %s' % (', '.join(cardNames))
        )
