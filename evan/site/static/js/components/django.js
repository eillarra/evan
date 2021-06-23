var DjangoComponents = {

  'django-form': {
    data: function () {
      return {
        mutable: {}
      };
    },
    props: {
      fields: {
        type: Array,
        default: function () {
          return [];
        }
      }
    },
    template: `
      <div class="row q-col-gutter-sm">
        <q-input dense filled v-for="f in fields" :name="f.name" :label="f.label" :type="f.type" :required="f.required" class="col-12" :class="f.class" v-model="mutable[f.name]" />
      </div>
    `
  }

};
