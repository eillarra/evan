var Store = new Vuex.Store({
    state: {
        saving: false,
        error: null,
        conference: null,
        coupons: [],
        registrations: []
    },
    getters: {
        currencySymbol: function (state) {
            if (!state.conference) return '';
            return {
                'EUR': '€',
                'USD': '$',
            }[state.conference.currency];
        },
        sessions: function (state) {
            if (!state.conference || state.conference.sessions == []) return [];
            return _.map(state.conference.sessions, function (obj) {
                track = _.find(state.conference.tracks, function (track) {
                    return track.id == obj.track;
                });
                obj._weekday = moment(obj.date).format('dddd');
                obj._track = (track) ? track.name : '';
                return obj;
            }).sort(function (a, b) {
                ma = (a.start_at) ? moment(a.date + 'T' + a.start_at) : moment(a.date + 'T07:00');
                mb = (b.start_at) ? moment(b.date + 'T' + b.start_at) : moment(b.date + 'T07:00');
                return ma - mb || textSort('title')(a, b);
            });
        },
        topics: function (state) {
            if (!state.conference || state.conference.topics == []) return [];
            return state.conference.topics.sort(textSort('name'));
        },
        tracks: function (state) {
            if (!state.conference || state.conference.tracks == []) return [];
            return state.conference.tracks.sort(textSort('name'));
        },
        usedCoupons: function (state) {
            if (state.registrations) return _.indexBy(_.map(state.registrations, function (obj) {
                return _.pick(obj, 'uuid', 'coupon');
            }), 'coupon');
            else return {};
        },
        valueRoom: function (state) {
            return function (id) {
                if (state.conference == []) return '';

                var venue = _.filter(state.conference.venues, function (venue) {
                    return _.some(venue.rooms, {id: id});
                })[0];

                return [
                    _.find(venue.rooms, function (room) {
                        return room.id == id;
                    }).name,
                    ', ',
                    venue.name
                ].join('');
            }
        }
    },
    mutations: {
        set: function (state, data) {
            state[data[0]] = data[1];
        },
        parseError: function (state, err) {
            state.error = getParsedErrors(err);
            state.saving = false;
        },
        startSaving: function (state, msg) {
            state.error = null;
            state.saving = msg;
        },
        endSaving: function (state, msg) {
            setTimeout(function () { state.saving = msg; }, DELAY / 2);
            setTimeout(function () { state.saving = false; }, DELAY);
        },
        getConference: function (state) {
            ajax().get($('#vue').data('url-conference')).then(function (res) {
                state.conference = res;
            });
        },
        getCoupons: function (state) {
            ajax().get($('#vue').data('url-coupons')).then(function (res) {
                state.coupons = res;
            });
        },
        getRegistrations: function (state) {
            ajax().get($('#vue').data('url-registrations')).then(function (res) {
                state.registrations = _.map(res, function (obj) {
                    obj._affiliation = (obj.user.profile.affiliation)
                        ? obj.user.profile.affiliation.toLowerCase()
                        : '';
                    obj._country = (obj.user.profile.country)
                        ? obj.user.profile.country.name.toLowerCase()
                        : '';
                    obj._invoice = (obj.invoice_requested) ? '+invoice' : '-invoice';
                    obj._name = (obj.user.first_name + ' ' + obj.user.last_name).toLowerCase();
                    obj._paid = (obj.is_paid) ? '+paid' : '-paid';
                    obj._visa = (obj.visa_requested) ? '+visa' : '-visa';
                    obj._date = moment(obj.created_at).format('lll');
                    return obj;
                });
            });
        }
    }
});

var ConferenceView = {
    template: '#v-conference',
    computed: _.extend(
        Vuex.mapState(['conference']), {
        dates: function () {
            if (!this.conference) return '';
            return [
                moment(this.conference.start_date).format('D'),
                moment(this.conference.end_date).format('D MMMM YYYY')
            ].join(' - ');
        },
        markedPresentation: function () {
            if (!this.conference.presentation) return '';
            return marked(this.conference.presentation, {sanitize: true});
        }
    }),
    methods: {
        update: _.debounce(function (e) {
            if (!e.target.checkValidity()) return;
            var data = _.omit(this.conference, ['code', 'country', 'sessions', 'topics', 'tracks', 'venues']);
            ajax().deput(this.$store, this.conference.url, data, 'Saving conference information...');
        }, DELAY)
    }
};

var CouponsView = {
    template: '#v-coupons',
    props: ['q'],
    data: function () {
        return {
            query: this.q || '',
            coupon: {value: 0, notes: ''}
        }
    },
    computed: _.extend(
        Vuex.mapState(['saving', 'coupons']),
        Vuex.mapGetters(['currencySymbol', 'usedCoupons']), {
        items: function () {
            var res = this.coupons.sort(textSort('notes'));

            if (q == '') return res;
            var q = this.query.toLowerCase();

            return res.filter(function (obj) {
                return obj.notes.toLowerCase().indexOf(q) !== -1
                    || obj.code.toLowerCase().indexOf(q) !== -1;
            });
        }
    }),
    methods: {
        create: function () {
            var self = this;
            self.$store.commit('startSaving', 'Creating new coupon...');
            ajax().post($('#vue').data('url-coupons'), self.coupon).done(function (res) {
                self.coupons.push(res);
                self.coupon = {value: 0, notes: ''};
                self.$store.commit('endSaving', 'Created!');
            }).fail(function (err) {
                self.$store.commit('parseError', err);
            });
        },
        update: _.debounce(function (coupon) {
            ajax().deput(this.$store, coupon.url, coupon, 'Saving changes to coupon...');
        }, DELAY),
        destroy: function (coupon) {
            var self = this;
            ajax().delete(coupon.url).done(function (res) {
                self.$store.commit('set', ['coupons', _.reject(self.coupons, function (obj) {
                    return coupon.id == obj.id;
                })]);
            });
        }
    },
    watch: {
        query: function (val, oldVal) {
            if (val != '') this.$router.replace({name: this.$route.name, query: {q: val}});
            else this.$router.replace({name: this.$route.name});
        }
    }
};

var FinancesView = {
    template: '#v-finances',
    computed: Vuex.mapState(['conference'])
};

var PapersView = {
    template: '#v-papers',
    props: ['q'],
    data: function () {
        return {
            query: this.q || '',
            message: null,
            paper: {title: '', authors: ''}
        }
    },
    computed: _.extend(
        Vuex.mapState(['saving', 'conference']), {
        items: function () {
            if (!this.conference) return [];
            res = this.conference.papers;

            if (q == '') return res;
            var q = this.query.toLowerCase();

            return res.filter(function (obj) {
                return obj.title.toLowerCase().indexOf(q) !== -1
                    || obj.authors.toLowerCase().indexOf(q) !== -1;
            });
        },
    }),
    methods: {
        create: function () {
            var self = this;
            self.$store.commit('startSaving', 'Creating new paper...');
            ajax().post($('#vue').data('url-papers'), self.paper).done(function (res) {
                self.conference.papers.push(res);
                self.paper = {title: '', authors: ''};
                self.$store.commit('endSaving', 'Created!');
            }).fail(function (err) {
                self.$store.commit('parseError', err);
            });
        },
        upload: function (e) {
            var self = this;
            var formData = new FormData(e.target);
            if (formData.get('csv').type != 'text/csv') {
                self.message = 'Please make sure that the uploaded file is in CSV format (text/csv).';
                return;
            };
            self.$store.commit('startSaving', 'Uploading papers from CSV...');
            ajax().upload($('#vue').data('url-papers-upload'), formData).done(function (res) {
                self.conference.papers = res;
                self.$store.commit('endSaving', 'Papers created!');
                self.message = null;
                e.target.reset();
                e.target.parentNode.click();  // Dismiss modal
            }).fail(function (err) {
                self.$store.commit('parseError', err);
            });
        },
        update: _.debounce(function (paper) {
            ajax().deput(this.$store, paper.url, paper, 'Saving changes to paper...');
        }, DELAY),
        destroy: function (paper) {
            var self = this;
            ajax().delete(paper.url).done(function (res) {
                self.conference.papers = _.reject(self.conference.papers, function (obj) {
                    return paper.id == obj.id;
                });
            });
        }
    },
    watch: {
        query: function (val, oldVal) {
            if (val != '') this.$router.replace({name: this.$route.name, query: {q: val}});
            else this.$router.replace({name: this.$route.name});
        }
    }
};

var RegistrationsView = {
    template: '#v-registrations',
    props: ['q'],
    data: function () {
        return {
            query: this.q || ''
        }
    },
    computed: _.extend(
        Vuex.mapState(['conference', 'registrations']), {
        items: function () {
            if (q == '') return this.registrations;
            var q = this.query.toLowerCase();

            return this.registrations.filter(function (obj) {
                return obj.user.email.toLowerCase().indexOf(q) !== -1
                    || obj.uuid.indexOf(q) !== -1
                    || obj._name.indexOf(q) !== -1
                    || obj._affiliation.indexOf(q) !== -1
                    || obj._country.indexOf(q) !== -1
                    || obj._paid.indexOf(q) !== -1
                    || obj._invoice.indexOf(q) !== -1
                    || obj._visa.indexOf(q) !== -1;
            });
        },
    }),
    watch: {
        query: function (val, oldVal) {
            if (val != '') this.$router.replace({name: this.$route.name, query: {q: val}});
            else this.$router.replace({name: this.$route.name});
        }
    }
};

var RegistrationDetailView = {
    template: '#v-registration-detail',
    props: ['uuid'],
    computed: _.extend(
        Vuex.mapState(['registrations']), {
        registration: function () {
            if (!this.registrations || this.registrations.length == 0) return null;
            return _.findWhere(this.registrations, {uuid: this.uuid});
        }
    })
};

var SessionsView = {
    template: '#v-sessions',
    props: ['q'],
    data: function () {
        return {
            query: this.q || '',
            session: {title: ''}
        }
    },
    computed: _.extend(
        Vuex.mapState(['saving', 'conference']),
        Vuex.mapGetters(['sessions']), {
        items: function () {
            if (q == '') return this.sessions;
            var q = this.query.toLowerCase();

            return this.sessions.filter(function (obj) {
                return obj.title.toLowerCase().indexOf(q) !== -1
                    || obj._weekday.toLowerCase().indexOf(q) !== -1
                    || obj.date.toLowerCase().indexOf(q) !== -1
                    || obj._track.toLowerCase().indexOf(q) !== -1;
            });
        }
    }),
    methods: {
        create: function () {
            var self = this;
            self.$store.commit('startSaving', 'Creating new session...');
            ajax().post($('#vue').data('url-sessions'), self.session).done(function (res) {
                self.conference.sessions.push(res);
                self.session = {title: ''};
                self.$store.commit('endSaving', 'Created!');
                self.$router.push({name: 'session-detail', params: {id: res.id}});
            }).fail(function (err) {
                self.$store.commit('parseError', err);
            });
        },
        update: _.debounce(function (session) {
            ajax().deput(this.$store, session.url, session, 'Saving session information...');
        }, DELAY)
    },
    watch: {
        query: function (val, oldVal) {
            if (val != '') this.$router.replace({name: this.$route.name, query: {q: val}});
            else this.$router.replace({name: this.$route.name});
        }
    }
};

var SessionDetailView = {
    template: '#v-session-detail',
    props: ['id'],
    computed: _.extend(
        Vuex.mapState(['conference']),
        Vuex.mapGetters(['sessions', 'topics', 'tracks', 'valueRoom']), {
        session: function () {
            if (this.sessions.length == 0) return null;
            return _.findWhere(this.sessions, {id: +this.id});
        },
        markedSummary: function () {
            if (this.session.summary == null) return '';
            return marked(this.session.summary, {sanitize: true});
        }
    }),
    methods: {
        update: _.debounce(function (session) {
            ajax().deput(this.$store, session.url, session, 'Saving session information...');
        }, DELAY),
        destroy: function (session) {
            var self = this;
            ajax().delete(session.url).done(function (res) {
                self.conference.sessions = _.reject(self.conference.sessions, function (obj) {
                    return session.id == obj.id;
                });
                self.$router.go(-1);
            });
        }
    }
};

var StatsView = {
    template: '#v-stats',
    computed: Vuex.mapState(['conference', 'registrations'])
};

var TaxonomyView = {
    template: '#v-taxonomy',
    data: function () {
        return {
            topic: {name: ''},
            track: {name: ''}
        }
    },
    computed: _.extend(
        Vuex.mapState(['saving', 'conference']),
        Vuex.mapGetters(['topics', 'tracks']), {
    }),
    methods: {
        createTopic: function () {
            var self = this;
            self.$store.commit('startSaving', 'Creating new topic...');
            ajax().post($('#vue').data('url-topics'), self.topic).done(function (res) {
                self.conference.topics.push(res);
                self.topic = {name: ''};
                self.$store.commit('endSaving', 'Created!');
            }).fail(function (err) {
                self.$store.commit('parseError', err);
            });
        },
        updateTopic: _.debounce(function (topic) {
            ajax().deput(this.$store, topic.url, topic, 'Saving changes to topic...');
        }, DELAY / 2),
        destroyTopic: function (topic) {
            var self = this;
            ajax().delete(topic.url).done(function (res) {
                self.conference.topics = _.reject(self.conference.topics, function (obj) {
                    return topic.id == obj.id;
                });
            });
        },
        createTrack: function () {
            var self = this;
            self.$store.commit('startSaving', 'Creating new track...');
            ajax().post($('#vue').data('url-tracks'), self.track).done(function (res) {
                self.conference.tracks.push(res);
                self.track = {name: ''};
                self.$store.commit('endSaving', 'Created!');
            }).fail(function (err) {
                self.$store.commit('parseError', err);
            });
        },
        updateTrack: _.debounce(function (track) {
            ajax().deput(this.$store, track.url, track, 'Saving changes to track...');
        }, DELAY),
        destroyTrack: function (track) {
            var self = this;
            ajax().delete(track.url).done(function (res) {
                self.conference.tracks = _.reject(self.conference.tracks, function (obj) {
                    return track.id == obj.id;
                });
            });
        },
    }
};

var VenuesView = {
    template: '#v-venues',
    data: function () {
        return {
            selected: 0,
            venue: {name: '', rooms: []},
            room: {name: '', max_capacity: 0}
        }
    },
    computed: _.extend(Vuex.mapState(['saving', 'conference']), {
        items: function () {
            if (this.conference == null) return [];
            return this.conference.venues.sort(textSort('name'));
        },
        selectedId: function () {
            if (this.selected > 0) return this.selected;
            if (this.conference == null && this.conference.venues.length > 0) return 0;
            else return this.items[0].id;
        }
    }),
    methods: {
        create: function () {
            var self = this;
            self.$store.commit('startSaving', 'Creating new venue...');
            ajax().post($('#vue').data('url-venues'), self.venue).done(function (res) {
                self.editingId = res.id;
                self.conference.venues.push(res);
                self.venue = {name: ''};
                self.$store.commit('endSaving', 'Created!');
            }).fail(function (err) {
                self.$store.commit('parseError', err);
            });
        },
        update: _.debounce(function (venue) {
            ajax().deput(this.$store, venue.url, venue, 'Saving changes to venue...');
        }, DELAY),
        destroy: function (venue) {
            var self = this;
            ajax().delete(venue.url).done(function (res) {
                self.conference.venues = _.reject(self.conference.venues, function (obj) {
                    return venue.id == obj.id;
                });
            });
        },
        createRoom: function (venue) {
            var self = this;
            self.$store.commit('startSaving', 'Creating new room...');
            ajax().post($('#vue').data('url-rooms'),
                {venue: venue.id, name: self.room.name, max_capacity: self.room.max_capacity}
            ).done(function (res) {
                venue.rooms.push(res);
                self.room = {name: '', max_capacity:0};
                self.$store.commit('endSaving', 'Created!');
            }).fail(function (err) {
                self.$store.commit('parseError', err);
            });
        },
        updateRoom: _.debounce(function (room) {
            ajax().deput(this.$store, room.url, room, 'Saving changes to room...');
        }, DELAY / 2),
        destroyRoom: function (venue, room) {
            var self = this;
            ajax().delete(room.url).done(function (res) {
                venue.rooms = _.reject(venue.rooms, function (obj) {
                    return room.id == obj.id;
                });
            });
        },
        staticmap: function (item) {
            return [
                'https://maps.googleapis.com/maps/api/staticmap',
                '?center=', item.lat, ',', item.lng,
                '&markers=color:0x039BE5%7C%7C', item.lat, ',', item.lng,
                '&zoom=16',
                '&size=600x300&scale=2',
                '&key=AIzaSyBFx2atP-hgXqq3ulRYDg9XFqfrRlqR4Q0'
            ].join('');
        }
    }
};

var Router = new VueRouter({
    routes: [
        {
            path: '/',
            redirect: {name: 'conference'}
        },
        {
            name: 'conference',
            path: '/conference/',
            pathToRegexpOptions: {strict: true},
            component: ConferenceView
        },
        {
            name: 'coupons',
            path: '/coupons/',
            pathToRegexpOptions: {strict: true},
            component: CouponsView,
            props: function (route) {
                return {q: route.query.q};
            }
        },
        {
            name: 'finances',
            path: '/finances/',
            pathToRegexpOptions: {strict: true},
            component: FinancesView
        },
        {
            name: 'papers',
            path: '/papers/',
            pathToRegexpOptions: {strict: true},
            component: PapersView,
            props: function (route) {
                return {q: route.query.q};
            }
        },
        {
            name: 'registrations',
            path: '/registrations/',
            pathToRegexpOptions: {strict: true},
            component: RegistrationsView,
            props: function (route) {
                return {q: route.query.q};
            }
        },
        {
            name: 'registration-detail',
            path: '/registrations/:uuid/',
            pathToRegexpOptions: {strict: true},
            component: RegistrationDetailView,
            props: true
        },
        {
            name: 'sessions',
            path: '/sessions/',
            pathToRegexpOptions: {strict: true},
            component: SessionsView,
            props: function (route) {
                return {q: route.query.q};
            }
        },
        {
            name: 'session-detail',
            path: '/sessions/:id/',
            pathToRegexpOptions: {strict: true},
            component: SessionDetailView,
            props: true
        },
        {
            name: 'stats',
            path: '/stats/',
            pathToRegexpOptions: {strict: true},
            component: StatsView
        },
        {
            name: 'taxonomy',
            path: '/taxonomy/',
            pathToRegexpOptions: {strict: true},
            component: TaxonomyView
        },
        {
            name: 'venues',
            path: '/venues/',
            pathToRegexpOptions: {strict: true},
            component: VenuesView
        }
    ],
    scrollBehavior: function (to, from, savedPosition) {
        return {x: 0, y: 0};
    }
});

var app = new Vue({
    el: '#vue',
    store: Store,
    router: Router,
    computed: Vuex.mapState(['saving', 'error', 'conference']),
    mounted: function () {
        $.when(
            this.$store.commit('getConference'),
            this.$store.commit('getCoupons'),
            this.$store.commit('getRegistrations')
        );
    }
});

$(document).keyup(function (e) {
    if (e.keyCode === 27 && ['registration-detail', 'session-detail'].indexOf(app.$route.name) !== -1) {
        app.$router.go(-1);
    }
});
