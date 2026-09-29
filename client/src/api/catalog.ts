import api from '@/api/client';
import type {
  BusinessTerm,
  BusinessTermPayload,
  CatalogEntry,
  MetricDefinition,
  MetricPayload,
  PublishTablePayload,
} from '@/lib/types';

export const catalogApi = {
  entries() {
    return api.get<CatalogEntry[]>('/catalog');
  },

  publish(payload: PublishTablePayload) {
    return api.post<CatalogEntry>('/catalog/publish', payload);
  },

  glossary() {
    return api.get<BusinessTerm[]>('/catalog/glossary');
  },

  createGlossary(payload: BusinessTermPayload) {
    return api.post<BusinessTerm>('/catalog/glossary', payload);
  },

  metrics() {
    return api.get<MetricDefinition[]>('/catalog/metrics');
  },

  createMetric(payload: MetricPayload) {
    return api.post<MetricDefinition>('/catalog/metrics', payload);
  },
};
