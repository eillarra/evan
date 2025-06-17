<template>
  <div>
    <div class="row q-col-gutter-md full-height">
      <div class="col-12 col-lg-6">
        <div class="column full-height">
          <q-input
            ref="textareaRef"
            v-model="internalValue"
            :label="label"
            dense
            autogrow
            bottom-slots
            @update:model-value="onInput"
          >
            <template v-slot:append>
              <div class="use-default-q-btn">
                <q-btn
                  flat
                  dense
                  :icon="iconAdd"
                  color="primary"
                  round
                  size="sm"
                  @click="openPaperSelector"
                  :tooltip="$t('program.insert_paper')"
                >
                  <q-tooltip>{{ $t('program.insert_paper') }}</q-tooltip>
                </q-btn>
              </div>
            </template>
            <template v-slot:hint>
              Use [paper:123] for database ID or [paperi:123] for internal ID references.<br />
              You can use Markdown to format your text; you can find more information about the
              <a href="https://commonmark.org/help/" target="_blank" rel="noopener">Markdown syntax here</a>.
            </template>
          </q-input>
          <div v-if="validation && !validation.is_valid" class="text-negative q-mt-sm">
            <div v-for="error in validation.errors" :key="error" class="text-caption">⚠️ {{ error }}</div>
          </div>
          <div v-if="orphanedPapers.length" class="q-mt-xl">
            <warning-banner type="warning">
              <strong>{{ orphanedPapers.length }} papers assigned but not referenced:</strong>
              <ul class="q-ma-none q-pl-md">
                <li v-for="paper in orphanedPapers" :key="paper.id" class="q-py-xs">
                  {{ paper.title }}
                  <q-btn
                    flat
                    dense
                    size="sm"
                    icon="link_off"
                    color="orange"
                    @click="unlinkPaper(paper)"
                    :title="$t('program.unlink_paper')"
                    class="q-ml-sm"
                  >
                    <q-tooltip>{{ $t('program.unlink_paper') }}</q-tooltip>
                  </q-btn>
                </li>
              </ul>
            </warning-banner>
          </div>
        </div>
      </div>
      <div class="col-12 col-lg-6">
        <div class="bg-grey-1 q-pa-md full-height">
          <program-preview :content="internalValue" :papers="papers" :empty-message="$t('program.preview_empty')" />
        </div>
      </div>
    </div>

    <q-dialog v-model="showPaperSelector" persistent>
      <q-card style="min-width: 600px">
        <q-card-section>
          <div class="text-h6">{{ $t('program.select_paper') }}</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model="paperSearchQuery" :placeholder="$t('program.search_papers')" outlined dense clearable>
            <template v-slot:prepend>
              <q-icon :name="iconSearch" />
            </template>
          </q-input>
          <div class="q-mt-md" style="max-height: 400px; overflow-y: auto">
            <q-list>
              <q-item
                v-for="paper in filteredPapers"
                :key="paper.id"
                class="paper-item"
                :class="{ disabled: isPaperUnavailable(paper) }"
                :disable="isPaperUnavailable(paper)"
              >
                <q-item-section>
                  <q-item-label class="text-weight-bold">{{ paper.title }}</q-item-label>
                  <q-item-label caption v-if="paper.extra_data?.authors_str">
                    {{ paper.extra_data.authors_str }}
                  </q-item-label>
                  <q-item-label caption v-if="paper.doi" class="text-primary"> DOI: {{ paper.doi }} </q-item-label>
                  <q-item-label caption v-if="isPaperUnavailable(paper)" class="text-orange">
                    Already assigned to {{ getAssignmentInfo(paper) }}
                  </q-item-label>
                  <q-item-label caption class="text-grey-6">
                    DB ID: {{ paper.id }}
                    <span v-if="paper.extra_data?.internal_id"> | Internal ID: {{ paper.extra_data.internal_id }}</span>
                  </q-item-label>
                </q-item-section>
                <q-item-section side v-if="!isPaperUnavailable(paper)">
                  <div class="q-gutter-xs use-default-q-btn">
                    <q-btn flat dense :icon="iconPaper" color="primary" @click="insertPaper(paper, 'db')">
                      <q-tooltip>Insert [paper:{{ paper.id }}]</q-tooltip>
                    </q-btn>
                    <q-btn
                      v-if="paper.extra_data?.internal_id"
                      flat
                      dense
                      :icon="iconPaper"
                      color="secondary"
                      @click="insertPaper(paper, 'internal')"
                    >
                      <q-tooltip>Insert [paperi:{{ paper.extra_data.internal_id }}]</q-tooltip>
                    </q-btn>
                  </div>
                </q-item-section>
              </q-item>
            </q-list>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat :label="$t('form.cancel')" @click="showPaperSelector = false" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { QInput } from 'quasar';

import ProgramPreview from '@/components/ProgramPreview.vue';
import WarningBanner from '@/components/ui/WarningBanner.vue';

import { iconAdd, iconPaper, iconSearch } from '@/icons';

interface Props {
  modelValue: string;
  label?: string;
  papers?: Paper[];
  renderedProgram?: string;
  validation?: {
    is_valid: boolean;
    errors: string[];
    paper_references: number[];
  };
  eventId?: number;
  itemId?: number;
  itemType?: 'session' | 'subsession';
  currentSession?: Session;
  currentSubsession?: Subsession;
}

interface Emits {
  (e: 'update:modelValue', value: string): void;
  (e: 'template-changed', value: string): void;
  (e: 'unlink-paper', paper: Paper): void;
}

const props = withDefaults(defineProps<Props>(), {
  label: 'Program',
  papers: () => [],
});

const emit = defineEmits<Emits>();

const internalValue = ref(props.modelValue);
const showPaperSelector = ref(false);
const paperSearchQuery = ref('');
const textareaRef = ref<QInput>();

// Update internal value when prop changes
watch(
  () => props.modelValue,
  (newVal) => {
    internalValue.value = newVal;
  },
  { immediate: true },
);

const filteredPapers = computed(() => {
  const papersToFilter = props.papers; // Show all papers in dialog, not just available ones

  if (!paperSearchQuery.value) return papersToFilter;

  const query = paperSearchQuery.value.toLowerCase();
  return papersToFilter.filter(
    (paper) =>
      paper.title.toLowerCase().includes(query) ||
      paper.extra_data?.authors_str?.toLowerCase().includes(query) ||
      paper.doi?.toLowerCase().includes(query),
  );
});

// Extract paper IDs referenced in current program
const referencedPaperIds = computed(() => {
  const paperMatches = internalValue.value.match(/\[paper:(\d+)\]/g) || [];
  const paperInternalMatches = internalValue.value.match(/\[paperi:([A-Za-z0-9_-]+)\]/g) || [];

  const paperIds: number[] = [];

  // Add direct database ID references
  paperMatches.forEach((match) => {
    const id = parseInt(match.match(/\d+/)![0]);
    paperIds.push(id);
  });

  // Add internal ID references (resolve to database IDs)
  paperInternalMatches.forEach((match) => {
    const internalId = match.match(/\[paperi:([A-Za-z0-9_-]+)\]/)![1];
    // Find paper with this internal_id
    const paper = props.papers.find((p) => {
      const paperInternalId = p.extra_data?.internal_id;
      return paperInternalId == internalId || paperInternalId === parseInt(internalId);
    });
    if (paper) {
      paperIds.push(paper.id);
    }
  });

  return [...new Set(paperIds)]; // Remove duplicates
});

// Papers assigned to current session/subsession but not referenced in program
const orphanedPapers = computed(() => {
  if (!props.currentSession && !props.currentSubsession) return [];

  return props.papers.filter((paper) => {
    // Check if paper is assigned to current session/subsession
    const isAssignedToCurrentItem = props.currentSubsession
      ? paper.subsession === props.currentSubsession.id
      : paper.session === props.currentSession?.id && !paper.subsession;

    // Return true if assigned but not referenced
    return isAssignedToCurrentItem && !referencedPaperIds.value.includes(paper.id);
  });
});

// Papers available for selection (exclude those assigned to other sessions)
const availablePapers = computed(() => {
  return props.papers.filter((paper) => {
    // Always allow unassigned papers
    if (!paper.session && !paper.subsession) return true;

    // Allow papers assigned to current session/subsession
    if (props.currentSubsession) {
      return (
        paper.subsession === props.currentSubsession.id ||
        (paper.session === props.currentSession?.id && !paper.subsession)
      );
    } else if (props.currentSession) {
      return paper.session === props.currentSession.id && !paper.subsession;
    }

    return false;
  });
});

// Check if a paper is unavailable for selection
function isPaperUnavailable(paper: Paper): boolean {
  return !availablePapers.value.includes(paper);
}

// Get assignment info for unavailable papers
function getAssignmentInfo(paper: Paper): string {
  // We'd need session/subsession data to show titles
  // For now, show IDs
  if (paper.subsession) {
    return `Session ${paper.session} → Subsession ${paper.subsession}`;
  }
  return `Session ${paper.session}`;
}

// Unlink a paper from current session/subsession
function unlinkPaper(paper: Paper) {
  // Emit event to parent component to handle the unlinking
  emit('unlink-paper', paper);
}

function onInput(value: string | number | null) {
  const stringValue = String(value || '');
  emit('update:modelValue', stringValue);
  emit('template-changed', stringValue);
}

function openPaperSelector() {
  paperSearchQuery.value = '';
  showPaperSelector.value = true;
}

function insertPaper(paper: Paper, idType: 'db' | 'internal' = 'db') {
  let paperRef: string;

  if (idType === 'internal' && paper.extra_data?.internal_id) {
    paperRef = `[paperi:${paper.extra_data.internal_id}]`;
  } else {
    paperRef = `[paper:${paper.id}]`;
  }

  // Try to get the native textarea element
  let textarea: HTMLTextAreaElement | null = null;

  if (textareaRef.value) {
    // Try different ways to access the native textarea
    textarea =
      textareaRef.value.$el?.querySelector('textarea') ||
      textareaRef.value.$refs?.input ||
      textareaRef.value.getNativeElement?.();
  }

  if (textarea && typeof textarea.selectionStart === 'number') {
    // Insert at cursor position
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const newValue = internalValue.value.substring(0, start) + paperRef + internalValue.value.substring(end);

    internalValue.value = newValue;
    emit('update:modelValue', newValue);
    emit('template-changed', newValue);

    // Set cursor position after inserted text
    setTimeout(() => {
      textarea!.focus();
      textarea!.setSelectionRange(start + paperRef.length, start + paperRef.length);
    }, 0);
  } else {
    // Fallback: append to end of current text
    const newValue = internalValue.value + (internalValue.value ? '\n' : '') + paperRef;
    internalValue.value = newValue;
    emit('update:modelValue', newValue);
    emit('template-changed', newValue);
  }

  showPaperSelector.value = false;
}
</script>

<style scoped>
.program-template-editor {
  width: 100%;
}

.program-textarea :deep(.q-field__control) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

.paper-item:hover:not(.disabled) {
  background-color: #f5f5f5;
}

.paper-item.disabled {
  opacity: 0.6;
}
</style>
