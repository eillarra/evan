NICE_DATE_FORMAT = 'dddd, MMM D'

function mapper() {
    return {
        events: function (items) {
            return items.map(function (obj) {
                var start = moment(obj.days[0].date);
                var end = moment(obj.days[obj.days.length - 1].date);
                var topicsDict = _.indexBy(obj.topics, 'id');
                var tracksDict = _.indexBy(obj.tracks, 'id');
                var roomsDict = {};
                _.each(obj.venues.slice(), function (venue) {
                    var v = _.omit(venue, 'rooms');
                    _.each(venue.rooms.slice(), function (room) {
                        var r = _.omit(room, 'venue');
                        r.venue = v;
                        roomsDict[room.id] = r;
                    });
                });
                obj.sessions.map(function (s) {
                    s.room = (_.has(roomsDict, s.room)) ? roomsDict[s.room] : null;
                    s.track = (_.has(tracksDict, s.track)) ? tracksDict[s.track] : null;
                    s.topics = s.topics.map(function (id) {
                        return topicsDict[id];
                    });
                    s.topicsDisplay = _.pluck(s.topics, 'name').join(', ');
                    s.startAt = moment(s.start_at, 'LTS').format('LT');
                    s.endAt = moment(s.end_at, 'LTS').format('LT');
                    s.niceDate = moment(s.date).format(NICE_DATE_FORMAT);
                    return s;
                });
                obj.dates = (start.isSame(end, 'day'))
                    ? start.format('MMMM D, YYYY')
                    : ((start.isSame(end, 'month'))
                        ? start.format('MMMM D') + '-' +  end.format('D, YYYY')
                        : start.format('MMMM D') + ' - ' +  end.format('MMMM D, YYYY')
                    );
                obj.days = obj.days.map(function (d) {
                    d.niceDate = moment(d.date).format(NICE_DATE_FORMAT);
                    return d;
                });
                obj.fees = obj.fees.map(function (f) {
                    f.isOneDay = f.type == 'one_day';
                    return f;
                });
                obj.deadline = moment(obj.registration_early_deadline);
                return obj;
            });
        },
        registrations: function (items) {
            return items.map(function (obj) {
                obj.totalFees = obj.base_fee + obj.extra_fees + obj.manual_extra_fees;
                obj.totalPaid = ((obj.coupon) ? obj.coupon.value : 0) + obj.paid + obj.paid_via_invoice;
                obj.isPaid = obj.totalPaid >= obj.totalFees;
                return obj;
            });
        }
    };
}
