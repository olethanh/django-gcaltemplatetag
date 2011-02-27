"""
Tags which can retrieve events from a public google calendar Atom feed,
and return the results for use in templates.

  Copyright (c) 2011, Olivier Le Thanh Duong <olivier@lethanh.be>

Based on django-template-utils :
  Copyright (c) 2009, James Bennett & Justin Quick

Based, in part, on the original idea by user baumer1122 and posted to
djangosnippets at http://www.djangosnippets.org/snippets/311/

"""

from django import template
from django.template.loader import render_to_string

import gdata.calendar.service
from datetime import datetime



calendar_service = gdata.calendar.service.CalendarService()

def get_feed(calendar_service, account, calendar='public'):
    start_date = datetime.now().strftime("%Y-%m-%d")
    query = gdata.calendar.service.CalendarEventQuery(account, calendar, 'full')
    query.start_min = start_date
    feed = calendar_service.CalendarQuery(query)
    return feed

def parse_date(date):
    try:
        if len(date) == len("YYYY-MM-DD"):
            d = datetime.strptime(date, "%Y-%m-%d")
        else :
            d = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.000+01:00")
        return d
    except Exception, e:
        return date

class EventItem(object):
    def __init__(self, event):
        """
        event : a gdata.calendar.CalendarEventEntry
        """
        self._event = event
        self._start_date = parse_date(event.when[0].start_time)
        self._title = event.title.text
        self._location = event.where[0].value_string
        self._link = event.GetHtmlLink().href

    def __str__(self):
        return "<EventItem: %s  on %s  at %s>" % (self._title, self._start_date, self._location)

    def title(self):
        return self._title

    def location(self):
        return self._location or 'bla'

    def start_date(self):
        return self._start_date
    def link(self):
        return self._link

class GcalIncludeNode(template.Node):
    def __init__(self, account, template_name, num_items=None):
        self.account = account
        self.num_items = int(num_items)
        self.template_name = template_name

    def render(self, context):
        feed = get_feed(calendar_service, self.account)
        event_items = [EventItem(event) for event in feed.entry[:self.num_items]]
        return render_to_string(self.template_name, { 'items': event_items,
                                                      'feed': feed })



def do_include_gcal(parser, token):
    """
    Parse an RSS or Atom feed and render a given number of its items
    into HTML.
    
    It is **highly** recommended that you use `Django's template
    fragment caching`_ to cache the output of this tag for a
    reasonable amount of time (e.g., one hour); polling a feed too
    often is impolite, wastes bandwidth and may lead to the feed
    provider banning your IP address.
    
    .. _Django's template fragment caching: http://www.djangoproject.com/documentation/cache/#template-fragment-caching
    
    Arguments should be:
    
    1. The account of the gcal to parse.
    
    2. The name of a template to use for rendering the results into HTML.
    
    3. The number of items to render (if not supplied, renders all
       items in the calendar).
       
    The template used to render the results will receive two variables:
    
    ``items``
        A list of object representing event items, each with
        'title', 'location', 'link' and 'start_date' members.
    
    ``feed``
        The feed itself, for pulling out arbitrary attributes.
    
    Requires python-gdata, which can be obtained at http://google.com.
    See `its documentation`_ for details of the parsed feed object.
    
    .. _its documentation: http://code.google.com/apis/calendar/data/1.0/developers_guide_python.html
    
    Syntax::
    
        {% include_gcal [account] [num_items] [template_name] %}
    
    Example::
    
        {% include_gcal bla@group.calendar.google.com 10 events/eventitems.html %}
    
    """
    bits = token.contents.split()
    if len(bits) == 3:
        return GcalIncludeNode(account=bits[1], template_name=bits[2])
    elif len(bits) == 4:
        return GcalIncludeNode(account=bits[1], template_name=bits[2], num_items=bits[3])
    else:
        raise template.TemplateSyntaxError("'%s' tag takes either two or three arguments" % bits[0])


register = template.Library()
register.tag('include_gcal', do_include_gcal)
