export interface FieldOption {
  value: string | number;
  label: string;
  description?: string;
  is_default?: boolean;
}

export interface ExtraDataField {
  code: string;
  label: string;
  field_type: string;
  required: boolean;
  show_for?: string[];
}

export interface SelectionCriteria {
  code: string;
  question: string;
  options: FieldOption[];
  depends_on?: [string, string[]];
  extra_data_fields?: ExtraDataField[];
}

export interface FeeSelectionConfig {
  criteria: SelectionCriteria[];
}
