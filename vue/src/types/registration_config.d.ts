interface ExtraDataField {
  code: string;
  label: string;
  field_type: string;
  required: boolean;
  show_for?: string[];
  show_when?: [string, string];
  options?: FieldOption[];
  description?: string;
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
  accompanying_persons: boolean;
  fee_selection: FeeSelectionConfig | null;
  form_fields: ExtraDataField[];
  program_session_selection?: boolean;
}
