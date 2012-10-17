#!/usr/bin/env python

"""Wrapper for the Strava (http://www.strava.com) API.

See https://stravasite-main.pbworks.com/w/browse/ for API documentation."""

__author__    = "Brian Landers"
__contact__   = "brian@packetslave.com"
__copyright__ = "Copyright 2012, Brian Landers"
__license__   = "Apache"
__version__   = "1.0"


BASE_API = "http://www.strava.com/api/v1"

from collections import defaultdict
from datetime import date, timedelta
import json

import sys

if sys.version_info < (3, 0):
    import urllib2
else:
    import urllib.request


class APIError(Exception):
    pass


class StravaObject(object):
    """Base class for interacting with the Strava API endpoint."""
    
    def __init__(self, oid):
        self._id = oid

    def load(self, url, key=None):
        if sys.version_info < (3, 0):
            try:
                req = urllib2.Request(BASE_API + url)
                rsp = urllib2.urlopen(req)
            except urllib2.HTTPError as e:
                raise APIError("%s: request failed: %s" % (url, e))
        else:
            try:
                rsp = urllib.request.urlopen(BASE_API + url)
            except urllib.error.HTTPError as e:
                raise APIError("%s: request failed: %s" % (url, e))
        txt = rsp.read().decode('utf-8')

        try:
            if key is not None:
                return json.loads(txt)[key]
            else:
                return json.loads(txt)
        except (ValueError, KeyError) as e:
            raise APIError("%s: parsing response failed: %s" % (url, e))

    @property
    def id(self):
        return self._id


class Athlete(StravaObject):
    """Encapsulates data about a single Athlete.

    Note that the athlete's name is NOT available through this API. You have to
    load a ride or effort to get that data from the service, and we don't want
    to make that heavy a query at the top level.
    """
    def __init__(self, oid):
        super(Athlete, self).__init__(oid)
        self._url = "/rides?athleteId=%s" % self.id

    def rides(self, start_date=None):
        out = []

        url = self._url
        if start_date:
            url += "&startDate=%s" % start_date.isoformat()
            
        for ride in self.load(url, "rides"):
            out.append(Ride(ride["id"], ride["name"]))

        return out
        
    def ride(self, ride_id):
        return next((ride for ride in self.rides() if ride.id == ride_id), None)

    def ride_stats(self, days=7):
        """Get number of rides, time, and distance for the past N days."""
        start = date.today() - timedelta(days=days)
        stats = defaultdict(float)
        
        for ride in self.rides(start_date=start):
            stats["rides"] += 1
            stats["moving_time"] += ride.detail.moving_time
            stats["distance"] += ride.detail.distance

        return stats
    
        
class Ride(StravaObject):
    """Information about a single ride.

    Most of the ride data is encapsulated in a RideDetail instance, accessible
    via the "detail" property. This lets us lazy-load the details, and saves an
    API round-trip if all we care about is the ID or name of the ride.
    """
    def __init__(self, oid, name):
        super(Ride, self).__init__(oid)
        self._name = name
        self._detail = None
        self._segments = []
        self._stream = None
        
    @property
    def name(self):
        return self._name

    @property
    def detail(self):
        if not self._detail:
            self._detail = RideDetail(self.id)
        return self._detail
        
    @property
    def stream(self):
        if not self._stream:
            self._stream = RideStream(self.id)
        return self._stream

    @property
    def segments(self):
        if not self._segments:
            for effort in self.load("/rides/%s/efforts" % self.id, "efforts"):
                self._segments.append(Segment(effort))
        return self._segments
        
        
class RideStream(StravaObject):
    """Detailed data points for a single ride.
        
    Possible keys returned from Strava:
        altitude
        altitude_original
        cadence
        distance
        grade_smooth
        heartrate
        latlng
        moving
        outlier
        resting
        temp
        time
        total_elevation
        velocity_smooth
        watts_calc
    """
    def __init__(self, oid):
        super(RideStream, self).__init__(oid)
        self._attr = self.load('/streams/%s' % oid)
    
    @property
    def altitude(self):
        return self.__try_get_values('altitude')
        
    @property
    def altitude_original(self):
        return self.__try_get_values('altitiude_original')
        
    @property
    def cadence(self):
        return self.__try_get_values('cadence')
    
    @property
    def distance(self):
    	return self.__try_get_values('distance')
    
    @property
    def grade_smooth(self):
        return self.__try_get_values('grade_smooth')
    
    @property
    def heartrate(self):
    	return self.__try_get_values('heartrate')
    
    @property
    def latlng(self):
        return self.__try_get_values('latlng')
    
    @property
    def moving(self):
        return self.__try_get_values('moving')
    
    @property
    def outlier(self):
        return self.__try_get_values('outlier')
    
    @property
    def resting(self):
        return self.__try_get_values('resting')
    
    @property
    def temp(self):
    	return self.__try_get_values('temp')
    
    @property
    def time(self):
        return self.__try_get_values('time')
    
    @property
    def total_elevation(self):
    	return self.__try_get_values('total_elevation')
    
    @property
    def watts_calc(self):
    	return self.__try_get_values('watts_calc')
    
    @property
    def velocity_smooth(self):
    	return self.__try_get_values('velocity_smooth')
        
    @property
    def raw_data(self):
        return self._attr
        
    def __try_get_values(self, key):
        # Not every rider has hardware to track every data point.
        # Need to make sure the requested data point is in
        # the stream before accessing it. Return an empty list
        # if the requested key isn't found in the stream.
        if key in self._attr:
            return self._attr[key]
        else:
            return []


class RideDetail(StravaObject):
    
    def __init__(self, oid):
        super(RideDetail, self).__init__(oid)
        self._attr = self.load("/rides/%s" % oid, 'ride')

    @property
    def athlete(self):
        return self._attr["athlete"]["name"]

    @property
    def athlete_id(self):
        return self._attr["athlete"]["id"]

    @property
    def bike(self):
        return self._attr["bike"]["name"]

    @property
    def bike_id(self):
        return self._attr["bike"]["id"]

    @property
    def location(self):
        return self._attr["location"]

    @property
    def distance(self):
        return self._attr["distance"]

    @property
    def moving_time(self):
        return self._attr["movingTime"]


class Segment(StravaObject):
    """Information about a single ride segment.

    Most of the data is encapsulated in a SegmentDetail instance, accessible via
    the "detail" property. This lets us lazy-load the details, and saves an API
    round-trip if all we care about is the ID or name of the segment.

    Note that this class combines the "effort" and "segment" as Strava defines
    them. They both ultimately pertain to a given portion of a ride, so it makes
    sense to access them both through the same interface.

    This does have the side effect, however, of requiring two API round-trips to
    load the "detail" property.  It's lazy-loaded, so if you just care about the
    segment name or ID, you won't take the it.
    """
    def __init__(self, attr):
        super(Segment, self).__init__(attr["id"])
        self._segment = attr["segment"]
        self._time = attr["elapsed_time"]
        self._detail = None
        
    @property
    def time(self):
        return self._time
    
    @property
    def name(self):
        return self._segment["name"]

    @property
    def detail(self):
        if not self._detail:
            self._detail = SegmentDetail(self._segment["id"], self.id)
        return self._detail


class SegmentDetail(StravaObject):
    def __init__(self, segment_id, effort_id):
        super(SegmentDetail, self).__init__(segment_id)
        self._effort_attr = self.load("/efforts/%s" % effort_id, "effort")
        self._segment_attr = self.load("/segments/%s" % segment_id, "segment")

    @property
    def distance(self):
        return self._segment_attr["distance"]

    @property
    def elapsed_time(self):
        return self._effort_attr["elapsedTime"]

    @property
    def moving_time(self):
        return self._effort_attr["movingTime"]

    @property
    def average_speed(self):
        return self._effort_attr["averageSpeed"]

    @property
    def maximum_speed(self):
        return self._effort_attr["maximumSpeed"]

    @property
    def average_watts(self):
        return self._effort_attr["averageWatts"]

    @property
    def average_grade(self):
        return self._segment_attr["averageGrade"]

    @property
    def climb_category(self):
        return self._segment_attr["climbCategory"]

    @property
    def elevations(self):
        return (self._segment_attr["elevationLow"],
                self._segment_attr["elevationHigh"],
                self._segment_attr["elevationGain"])
