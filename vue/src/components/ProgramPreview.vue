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
  emptyMessage?: string;
  showAuthors?: boolean;
  showInternalIds?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  papers: () => [],
  showAuthors: true,
  showInternalIds: true,
});

const processedContent = computed(() => {
  if (!props.content?.trim()) return '';

  // Process paper references and return the text for MarkedDiv to handle markdown
  return replacePaperReferences(props.content);
});

function replacePaperReferences(text: string): string {
  let result = text;

  const paperRefPattern = /\[paper:(\d+)\]/g;
  result = result.replace(paperRefPattern, (_, paperId) => {
    const paper = props.papers.find((p) => p.id === parseInt(paperId));
    if (paper) {
      return formatPaperReference(paper, false);
    }
    return `**[Paper ${paperId} not found]**`;
  });

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
