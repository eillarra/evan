var ProfileMixin = {
  data: function () {
    return {
      genderOptions: EvanMetadata.getQuasarOptions('gender'),
      dietaryOptions: EvanMetadata.getQuasarOptions('dietary')
    };
  },
  computed: _.extend(
    Vuex.mapState(['user']), {
    countryName: function () {
      return this.user.profile.country.name;
    },
    hasCase: function () {
      return (/^[A-Z]*$/).test(this.user.first_name)
        || (/^[A-Z]*$/).test(this.user.last_name);
    }
  }),
  methods: {
    update: function () {
      Evan.api.update(this.user);
    }
  }
};
