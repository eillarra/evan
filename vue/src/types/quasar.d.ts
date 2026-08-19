interface QuasarSelectOption {
  value: boolean | string | number | null;
  label: string;
  disable?: boolean;
}

interface QuasarTableColumn {
  name: string;
  label: string | null;
  field: string | ((row: unknown) => unknown);
  align?: 'left' | 'right' | 'center' | undefined;
  sortable?: boolean | undefined;
  sort?: ((a: unknown, b: unknown, rowA: unknown, rowB: unknown) => number) | undefined;
  classes?: string;
  style?: string;
  headerClasses?: string;
  headerStyle?: string;
}
