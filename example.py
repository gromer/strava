#!/usr/bin/env python

# Athlete is Craig Peters, employee at Strava
# http://app.strava.com/athletes/103227

from strava import Athlete

"""
First, we set up a Strava Object for the Athlete that we want to query
"""

st = Athlete(103227)

"""
Once we've gotten the Athlete's object, we can then look at various
statistics - number of rides and total moving time are shown below.
By default, we only look at the last 7 days.
"""

print('Ridden %d rides' % st.ride_stats()['rides'])
print('Total moving time: %f minutes' % \
    (float(st.ride_stats()['moving_time']) / 60.0))

"""
We can then iterate through the rides, and further through the segments on
each of those rides, displaying information from each. Ride details are stored
in metric, so, we need to convert that to get imperial measurements.
"""

for ride in st.rides():
    print('Ride name: %s' % ride.name)
    for segment in ride.segments:
        print('  Segment: %s\n    Moving Time: %f minutes\n    Average ' \
            'Speed: %f mph' % \
            (segment.name, segment.detail.moving_time / 60.0, \
            segment.detail.average_speed * 0.000621))

"""
We can also get a lot of details data points from a ride.
"""
if len(st.rides()) > 0:
    ride = st.rides()[0]
    
    print 'Max altitude: %sm.' % min(ride.stream.altitude)
    print 'Max altitude: %sm.' % max(ride.stream.altitude)
    
    if len(ride.stream.temp) > 0:
        # Calculate the average (in Celsius)
        c = sum(ride.stream.temp) / len(ride.stream.temp)
        
        # Convert the Celsius average to Fahrenheit
        f = ((c * 9) / 5) + 32
        
        print 'Avg temp: %s Fahrenheit' % f
    