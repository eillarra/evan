import { ref, computed } from 'vue';
import { useStore } from '@/apps/event/store';

interface ProgramValidation {
  is_valid: boolean;
  errors: string[];
  paper_references: number[];
  keynote_references: string[];
}

interface PaperInfo {
  id: number;
  title: string;
  authors: string;
  abstract?: string;
}

interface KeynoteInfo {
  id: number;
  code: string;
  title: string;
  speaker: string;
  abstract?: string;
}

interface Author {
  name: string;
}

export function useProgramTemplate() {
  const store = useStore();
  const validationCache = ref<Map<string, ProgramValidation>>(new Map());
  const renderedCache = ref<Map<string, string>>(new Map());
  const isValidating = ref(false);
  const isRendering = ref(false);

  function findPaper(paperId: number): PaperInfo | null {
    const paper = store.papers.find((p) => p.id === paperId);
    if (!paper) return null;

    return {
      id: paper.id,
      title: paper.title,
      authors:
        paper.extra_data?.authors_str ||
        paper.extra_data?.authors?.map((author: Author) => author.name).join(', ') ||
        'Unknown authors',
      abstract: paper.abstract,
    };
  }

  function findPaperByInternalId(internalId: string): PaperInfo | null {
    const paper = store.papers.find((p) => {
      const extraData = p.extra_data;
      if (!extraData?.internal_id) return false;

      // Try exact match first
      if (extraData.internal_id === internalId) return true;

      // Try as number comparison if both can be converted
      const numericInternal =
        typeof extraData.internal_id === 'number' ? extraData.internal_id : parseInt(String(extraData.internal_id), 10);
      const numericSearch = parseInt(internalId, 10);

      return !isNaN(numericInternal) && !isNaN(numericSearch) && numericInternal === numericSearch;
    });

    if (!paper) return null;

    return {
      id: paper.id,
      title: paper.title,
      authors:
        paper.extra_data?.authors_str ||
        paper.extra_data?.authors?.map((author: Author) => author.name).join(', ') ||
        'Unknown authors',
      abstract: paper.abstract,
    };
  }

  function formatPaperReference(paper: PaperInfo, includeAuthors: boolean = true): string {
    let result = `**${paper.title}**`;
    if (includeAuthors && paper.authors) {
      result += `  \n*${paper.authors}*`;
    }
    return result;
  }

  function findKeynote(keynoteCode: string): KeynoteInfo | null {
    const keynote = store.keynotes.find((k) => k.code === keynoteCode);
    if (!keynote) return null;

    return {
      id: keynote.id,
      code: keynote.code,
      title: keynote.title,
      speaker: keynote.speaker,
      abstract: keynote.abstract,
    };
  }

  function formatKeynoteReference(keynote: KeynoteInfo): string {
    return `**${keynote.title}** - *${keynote.speaker}*`;
  }

  async function validateTemplate(template: string): Promise<ProgramValidation> {
    if (!template.trim()) {
      return { is_valid: true, errors: [], paper_references: [], keynote_references: [] };
    }

    const cacheKey = template;
    if (validationCache.value.has(cacheKey)) {
      return validationCache.value.get(cacheKey)!;
    }

    isValidating.value = true;
    try {
      const paperRefs = extractPaperReferences(template);
      const keynoteRefs = extractKeynoteReferences(template);
      const errors: string[] = [];

      // Validate [paper:ID] references
      const directMatches = template.match(/\[paper:(\d+)\]/g);
      if (directMatches) {
        for (const match of directMatches) {
          const idMatch = match.match(/\[paper:(\d+)\]/);
          if (idMatch) {
            const paperId = parseInt(idMatch[1], 10);
            const paper = findPaper(paperId);
            if (!paper) {
              errors.push(`Paper ${paperId} not found`);
            }
          }
        }
      }

      // Validate [paperi:ID] references
      const internalMatches = template.match(/\[paperi:([A-Za-z0-9_-]+)\]/g);
      if (internalMatches) {
        for (const match of internalMatches) {
          const idMatch = match.match(/\[paperi:([A-Za-z0-9_-]+)\]/);
          if (idMatch) {
            const internalId = idMatch[1];
            const paper = findPaperByInternalId(internalId);
            if (!paper) {
              errors.push(`Paper with internal ID ${internalId} not found`);
            }
          }
        }
      }

      // Validate [keynote:CODE] references
      const keynoteMatches = template.match(/\[keynote:([A-Za-z0-9_-]+)\]/g);
      if (keynoteMatches) {
        for (const match of keynoteMatches) {
          const codeMatch = match.match(/\[keynote:([A-Za-z0-9_-]+)\]/);
          if (codeMatch) {
            const keynoteCode = codeMatch[1];
            const keynote = findKeynote(keynoteCode);
            if (!keynote) {
              errors.push(`Keynote ${keynoteCode} not found`);
            }
          }
        }
      }

      const validation: ProgramValidation = {
        is_valid: errors.length === 0,
        errors,
        paper_references: paperRefs,
        keynote_references: keynoteRefs,
      };

      validationCache.value.set(cacheKey, validation);
      return validation;
    } catch (error) {
      const validation: ProgramValidation = {
        is_valid: false,
        errors: ['Validation error'],
        paper_references: [],
        keynote_references: [],
      };
      return validation;
    } finally {
      isValidating.value = false;
    }
  }

  async function renderTemplate(template: string): Promise<string> {
    if (!template.trim()) {
      return '';
    }

    const cacheKey = template;
    if (renderedCache.value.has(cacheKey)) {
      return renderedCache.value.get(cacheKey)!;
    }

    isRendering.value = true;
    try {
      let rendered = template;

      // Process [paper:ID] references (database IDs)
      const paperMatches = template.match(/\[paper:(\d+)\]/g);
      if (paperMatches) {
        for (const match of paperMatches) {
          const idMatch = match.match(/\[paper:(\d+)\]/);
          if (idMatch) {
            const paperId = parseInt(idMatch[1], 10);
            const paper = findPaper(paperId);
            if (paper) {
              const paperMarkdown = formatPaperReference(paper);
              rendered = rendered.replace(new RegExp(`\\[paper:${paperId}\\]`, 'g'), paperMarkdown);
            } else {
              rendered = rendered.replace(new RegExp(`\\[paper:${paperId}\\]`, 'g'), `**Paper ${paperId} not found**`);
            }
          }
        }
      }

      // Process [paperi:ID] references (internal IDs)
      const internalMatches = template.match(/\[paperi:([A-Za-z0-9_-]+)\]/g);
      if (internalMatches) {
        for (const match of internalMatches) {
          const idMatch = match.match(/\[paperi:([A-Za-z0-9_-]+)\]/);
          if (idMatch) {
            const internalId = idMatch[1];
            const paper = findPaperByInternalId(internalId);
            if (paper) {
              const paperMarkdown = formatPaperReference(paper);
              rendered = rendered.replace(
                new RegExp(`\\[paperi:${internalId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]`, 'g'),
                paperMarkdown,
              );
            } else {
              rendered = rendered.replace(
                new RegExp(`\\[paperi:${internalId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]`, 'g'),
                `**Paper i${internalId} not found**`,
              );
            }
          }
        }
      }

      // Process [keynote:CODE] references
      const keynoteMatches = template.match(/\[keynote:([A-Za-z0-9_-]+)\]/g);
      if (keynoteMatches) {
        for (const match of keynoteMatches) {
          const codeMatch = match.match(/\[keynote:([A-Za-z0-9_-]+)\]/);
          if (codeMatch) {
            const keynoteCode = codeMatch[1];
            const keynote = findKeynote(keynoteCode);
            if (keynote) {
              const keynoteMarkdown = formatKeynoteReference(keynote);
              rendered = rendered.replace(
                new RegExp(`\\[keynote:${keynoteCode.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]`, 'g'),
                keynoteMarkdown,
              );
            } else {
              rendered = rendered.replace(
                new RegExp(`\\[keynote:${keynoteCode.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]`, 'g'),
                `**Keynote ${keynoteCode} not found**`,
              );
            }
          }
        }
      }

      renderedCache.value.set(cacheKey, rendered);
      return rendered;
    } catch (error) {
      console.error('Error rendering template:', error);
      return template; // Fallback to original template
    } finally {
      isRendering.value = false;
    }
  }

  function extractPaperReferences(template: string): number[] {
    const paperIds: number[] = [];

    // Extract [paper:ID] references (database IDs)
    const directMatches = template.match(/\[paper:(\d+)\]/g);
    if (directMatches) {
      for (const match of directMatches) {
        const idMatch = match.match(/\[paper:(\d+)\]/);
        if (idMatch) {
          const paperId = parseInt(idMatch[1], 10);
          if (paperId > 0) {
            paperIds.push(paperId);
          }
        }
      }
    }

    // Extract [paperi:ID] references (internal IDs) and resolve to database IDs
    const internalMatches = template.match(/\[paperi:([A-Za-z0-9_-]+)\]/g);
    if (internalMatches) {
      for (const match of internalMatches) {
        const idMatch = match.match(/\[paperi:([A-Za-z0-9_-]+)\]/);
        if (idMatch) {
          const internalId = idMatch[1];
          const paper = findPaperByInternalId(internalId);
          if (paper) {
            paperIds.push(paper.id);
          }
        }
      }
    }

    return Array.from(new Set(paperIds)); // Remove duplicates
  }

  function extractKeynoteReferences(template: string): string[] {
    const keynoteCodes: string[] = [];

    // Extract [keynote:CODE] references
    const keynoteMatches = template.match(/\[keynote:([A-Za-z0-9_-]+)\]/g);
    if (keynoteMatches) {
      for (const match of keynoteMatches) {
        const codeMatch = match.match(/\[keynote:([A-Za-z0-9_-]+)\]/);
        if (codeMatch) {
          const keynoteCode = codeMatch[1];
          keynoteCodes.push(keynoteCode);
        }
      }
    }

    return Array.from(new Set(keynoteCodes)); // Remove duplicates
  }

  function clearCache() {
    validationCache.value.clear();
    renderedCache.value.clear();
  }

  return {
    validateTemplate,
    renderTemplate,
    extractPaperReferences,
    extractKeynoteReferences,
    clearCache,
    isValidating: computed(() => isValidating.value),
    isRendering: computed(() => isRendering.value),
  };
}
