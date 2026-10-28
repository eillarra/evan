import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, type PropType } from 'vue';

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}));

vi.mock('@/axios.ts', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('@/utils/notify', () => ({
  notify: { success: vi.fn(), info: vi.fn(), error: vi.fn() },
}));

vi.mock('@/utils/dialog', () => ({ confirm: vi.fn() }));

import { useStore } from '../../../store';

import SponsorsTable from '../SponsorsTable.vue';

interface TableColumn {
  name: string;
  label?: string;
  sort?: (a: string | number, b: string | number) => number;
}

interface TableRow {
  name: string;
  level: string | number;
}

// The table only consumes the column contract: `DataTable` hands the columns,
// rows and initial sort to q-table, so stubbing it keeps this a behavioural
// test of what `SponsorsTable` passes down.
const DataTableStub = defineComponent({
  name: 'DataTable',
  props: {
    columns: { type: Array as PropType<TableColumn[]>, required: true },
    rows: { type: Array as PropType<TableRow[]>, required: true },
    sortBy: { type: String, default: undefined },
  },
  setup() {
    return () => h('div', { class: 'data-table-stub' });
  },
});

function makeSponsor(id: number, name: string, level: number): Sponsor {
  return { id, name, website: '', level, files: [] } as unknown as Sponsor;
}

// Prop order is neither the configured tier order nor alphabetical.
const DEFAULT_SPONSORS = [
  makeSponsor(1, 'Bronze Backer', 2),
  makeSponsor(2, 'Gold Backer', 0),
  makeSponsor(3, 'Silver Backer', 1),
];

function mountTable(sponsorTypes: string[], sponsors = DEFAULT_SPONSORS) {
  const pinia = createPinia();
  setActivePinia(pinia);
  const store = useStore();
  store.evanEvent = { extra_data: { sponsor_types: sponsorTypes } } as unknown as ManagedEvanEvent;

  const wrapper = mount(SponsorsTable, {
    props: { sponsors },
    global: {
      plugins: [pinia],
      stubs: { DataTable: DataTableStub },
    },
  });

  const table = wrapper.findComponent(DataTableStub);

  return {
    columns: table.props('columns') as TableColumn[],
    rows: table.props('rows') as TableRow[],
    sortBy: table.props('sortBy') as string | undefined,
  };
}

describe('SponsorsTable level column', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('sorts by the configured tier order instead of the displayed label', () => {
    const { columns, rows, sortBy } = mountTable(['Gold', 'Silver', 'Bronze']);

    const levelColumn = columns.find((column) => column.name === 'level');
    expect(levelColumn?.label).toBe('fields.type');
    expect(sortBy).toBe('level');

    // Display is unchanged: the configured tier label replaces the numeric level.
    const displayed = rows.map((row) => row.level);
    expect(displayed).toEqual(['Bronze', 'Gold', 'Silver']);

    // Sorting must follow the configured order (Gold, Silver, Bronze), which the
    // labels themselves do not: alphabetically that would be Bronze, Gold, Silver.
    expect(typeof levelColumn?.sort).toBe('function');
    expect([...displayed].sort(levelColumn!.sort!)).toEqual(['Gold', 'Silver', 'Bronze']);
  });

  it('keeps the numeric level order when no sponsor types are configured', () => {
    const { columns, rows } = mountTable([]);

    const levelColumn = columns.find((column) => column.name === 'level');
    expect(levelColumn?.label).toBe('fields.order');

    // Display is unchanged: without configured tiers the raw level is shown.
    const displayed = rows.map((row) => row.level);
    expect(displayed).toEqual([2, 0, 1]);

    const ordered = levelColumn?.sort ? [...displayed].sort(levelColumn.sort) : [...displayed].sort();
    expect(ordered).toEqual([0, 1, 2]);
  });

  it('orders multi-digit levels numerically when no types are configured', () => {
    const { columns, rows } = mountTable([], [makeSponsor(1, 'Later', 10), makeSponsor(2, 'Earlier', 2)]);

    const levelColumn = columns.find((column) => column.name === 'level');

    expect([...rows.map((row) => row.level)].sort(levelColumn!.sort!)).toEqual([2, 10]);
  });
});
