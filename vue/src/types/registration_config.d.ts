interface ExtraDataField {
  code: string;
  label: string;
  field_type: string;
  required: boolean;
  show_for?: string[];
}

interface SelectionCriteria {
  code: string;
  question: string;
  options: FieldOption[];
  depends_on?: [string, string[]];
  extra_data_fields?: ExtraDataField[];
}

interface FeeSelectionConfig {
  criteria: SelectionCriteria[];
}

interface EvanEventRegistrationConfig {
  fee_selection: FeeSelectionConfig | null;
}
