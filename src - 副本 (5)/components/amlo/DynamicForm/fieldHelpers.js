/**
 * Shared helpers for AMLO dynamic form field metadata.
 * Normalises backend payloads so legacy components can operate
 * without knowing whether values came from SQLAlchemy rows or
 * preprocessed schema builders.
 */

/**
 * Derive a human friendly label for a field.
 * @param {Object} field
 * @returns {string}
 */
export function resolveFieldLabel(field = {}) {
  return (
    field.field_label ||
    field.label ||
    field.field_cn_name ||
    field.field_en_name ||
    field.field_th_name ||
    field.field_name ||
    ''
  );
}

/**
 * Parse validation rules regardless of the underlying shape.
 * Newer APIs send a JSON object while older code persisted the
 * payload as a string – handle both to keep compatibility.
 * @param {Object} field
 * @returns {Object}
 */
export function readValidationRules(field = {}) {
  const candidate =
    field.validation_rule ??
    field.validation_rules ??
    field.validationRules ??
    null;

  if (!candidate) {
    return {};
  }

  if (typeof candidate === 'object') {
    return candidate;
  }

  if (typeof candidate === 'string') {
    try {
      return JSON.parse(candidate);
    } catch (_error) {
      return {};
    }
  }

  return {};
}

/**
 * Normalise a single field definition so downstream components
 * can rely on consistent keys.
 * @param {Object} field
 * @returns {Object}
 */
export function normalizeFieldDefinition(field = {}) {
  if (!field || typeof field !== 'object') {
    return field;
  }

  const normalized = { ...field };

  const label = resolveFieldLabel(normalized);
  normalized.field_label = label;
  normalized.label = label;

  const rules = readValidationRules(normalized);
  normalized.validation_rule = rules;
  normalized.validation_rules = JSON.stringify(rules);

  if (typeof normalized.is_required !== 'undefined') {
    normalized.is_required = Boolean(normalized.is_required);
  }

  if (typeof normalized.is_readonly !== 'undefined') {
    normalized.is_readonly = Boolean(normalized.is_readonly);
  }

  return normalized;
}

/**
 * Normalise every field inside a group structure.
 * @param {Object} group
 * @returns {Object}
 */
export function normalizeFieldGroup(group = {}) {
  if (!group || typeof group !== 'object') {
    return group;
  }

  const fields = Array.isArray(group.fields)
    ? group.fields.map(normalizeFieldDefinition)
    : [];

  return {
    ...group,
    fields,
  };
}
