import { ref, computed } from 'vue';
import { api } from '@/axios';

interface ProgramValidation {
  is_valid: boolean;
  errors: string[];
  paper_references: number[];
}

export function useProgramTemplate(sessionId: number, eventApiUrl: string) {
  const validationCache = ref<Map<string, ProgramValidation>>(new Map());
  const renderedCache = ref<Map<string, string>>(new Map());
  const isValidating = ref(false);
  const isRendering = ref(false);

  async function validateTemplate(template: string): Promise<ProgramValidation> {
    if (!template.trim()) {
      return { is_valid: true, errors: [], paper_references: [] };
    }

    const cacheKey = `${sessionId}-${template}`;
    if (validationCache.value.has(cacheKey)) {
      return validationCache.value.get(cacheKey)!;
    }

    isValidating.value = true;
    try {
      // For now, we'll do client-side validation
      // In the future, you could add an API endpoint for server-side validation
      const paperRefs = extractPaperReferences(template);
      const validation: ProgramValidation = {
        is_valid: true,
        errors: [],
        paper_references: paperRefs,
      };

      validationCache.value.set(cacheKey, validation);
      return validation;
    } catch (error) {
      const validation: ProgramValidation = {
        is_valid: false,
        errors: ['Validation error'],
        paper_references: [],
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

    const cacheKey = `${sessionId}-${template}`;
    if (renderedCache.value.has(cacheKey)) {
      return renderedCache.value.get(cacheKey)!;
    }

    isRendering.value = true;
    try {
      // Get the session with rendered program
      const response = await api.get(`${eventApiUrl}sessions/${sessionId}/`, {
        params: { _t: Date.now() }, // Cache busting
      });

      const rendered = response.data.rendered_program || template;
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
    const matches = template.match(/\[paper:(\d+)\]/g);
    if (!matches) return [];

    return matches
      .map((match) => {
        const idMatch = match.match(/\[paper:(\d+)\]/);
        return idMatch ? parseInt(idMatch[1], 10) : 0;
      })
      .filter((id) => id > 0);
  }

  function clearCache() {
    validationCache.value.clear();
    renderedCache.value.clear();
  }

  return {
    validateTemplate,
    renderTemplate,
    extractPaperReferences,
    clearCache,
    isValidating: computed(() => isValidating.value),
    isRendering: computed(() => isRendering.value),
  };
}
