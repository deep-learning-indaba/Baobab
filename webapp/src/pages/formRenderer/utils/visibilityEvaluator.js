/**
 * Frontend visibility evaluator for tag-based visibility expressions
 */

export function evaluateVisibilityExpression(expression, userTags) {
  if (!expression) {
    return true;
  }

  const operator = expression.operator;

  if (operator === 'AND' || operator === 'OR' || operator === 'NOT') {
    return evaluateLogicalOperator(expression, userTags);
  }

  const tag = expression.tag;
  if (tag) {
    return userTags.includes(tag);
  }

  return false;
}

function evaluateLogicalOperator(expression, userTags) {
  const operator = expression.operator;
  const conditions = expression.conditions || [];

  if (operator === 'AND') {
    return conditions.every(cond => evaluateVisibilityExpression(cond, userTags));
  }

  if (operator === 'OR') {
    return conditions.some(cond => evaluateVisibilityExpression(cond, userTags));
  }

  if (operator === 'NOT') {
    if (conditions.length !== 1) {
      console.warn('NOT operator expects exactly 1 condition, got', conditions.length);
      return false;
    }
    return !evaluateVisibilityExpression(conditions[0], userTags);
  }

  return false;
}
