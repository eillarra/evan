<template>
  <marked-div v-if="processedContent" :text="processedContent" />
  <marked-div v-else :text="emptyMessage || 'No program content'" />
</template>

<script setup lang="ts">
import { computed } from 'vue';

import MarkedDiv from '@/components/MarkedDiv.vue';

interface Props {
  content: string;
  papers?: Paper[];
  keynotes?: Keynote[];
  emptyMessage?: string;
  showAuthors?: boolean;
  showInternalIds?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  papers: () => [],
  keynotes: () => [],
  showAuthors: true,
  showInternalIds: true,
});

const processedContent = computed(() => {
  if (!props.content?.trim()) return '';

  // Process paper and keynote references and return the text for MarkedDiv to handle markdown
  return replaceAllReferences(props.content);
});

function replaceAllReferences(text: string): string {
  let result = text;

  // Process [paper:ID] references
  const paperRefPattern = /\[paper:(\d+)\]/g;
  result = result.replace(paperRefPattern, (_, paperId) => {
    const paper = props.papers.find((p) => p.id === parseInt(paperId));
    if (paper) {
      return formatPaperReference(paper, false);
    }
    return `**[Paper ${paperId} not found]**`;
  });

  // Process [paperi:ID] references
  const paperInternalRefPattern = /\[paperi:(\d+)\]/g;
  result = result.replace(paperInternalRefPattern, (_, internalId) => {
    const targetId = parseInt(internalId);
    const paper = props.papers.find((p) => {
      const paperInternalId = p.extra_data?.internal_id;
      return paperInternalId === targetId || paperInternalId === internalId;
    });

    if (paper) {
      return formatPaperReference(paper, true, internalId);
    }
    return `**[Paper i${internalId} not found]**`;
  });

  // Process [keynote:CODE] references
  const keynoteRefPattern = /\[keynote:([A-Za-z0-9_-]+)\]/g;
  result = result.replace(keynoteRefPattern, (_, keynoteCode) => {
    const keynote = props.keynotes.find((k) => k.code === keynoteCode);
    if (keynote) {
      return formatKeynoteReference(keynote);
    }
    return `**[Keynote ${keynoteCode} not found]**`;
  });

  return result;
}

function formatPaperReference(paper: Paper, isInternal: boolean, internalId?: string): string {
  // Normalize whitespace to remove line breaks and extra spaces
  const normalizedTitle = normalizeWhitespace(paper.title);
  let formatted = `**${normalizedTitle}**`;

  if (props.showAuthors && paper.extra_data?.authors_str) {
    const normalizedAuthors = normalizeWhitespace(paper.extra_data.authors_str);
    formatted += ` *(${normalizedAuthors})*`;
  }

  if (isInternal && props.showInternalIds && internalId) {
    formatted += ` *[#${internalId}]*`;
  }

  return formatted;
}

function formatKeynoteReference(keynote: Keynote): string {
  const normalizedTitle = normalizeWhitespace(keynote.title);
  const normalizedSpeaker = normalizeWhitespace(keynote.speaker);
  return `**${normalizedTitle}** - *${normalizedSpeaker}*`;
}

function normalizeWhitespace(text: string): string {
  // Replace line breaks and multiple spaces with single spaces, then trim
  return text.replace(/\s+/g, ' ').trim();
}
</script>

<style scoped>
.program-preview {
  width: 100%;
}
</style>
