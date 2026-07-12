/**
 * Dependency evaluator for the frontend - mirrors the backend DependencyEvaluator
 * Evaluates dependency expressions against answer values to determine visibility
 */

const DependencyOperator = {
  // Comparison operators
  EQUALS: 'EQUALS',
  NOT_EQUALS: 'NOT_EQUALS',
  IN: 'IN',
  NOT_IN: 'NOT_IN',
  
  // Numeric operators
  GREATER_THAN: 'GREATER_THAN',
  LESS_THAN: 'LESS_THAN',
  GREATER_THAN_OR_EQUAL: 'GREATER_THAN_OR_EQUAL',
  LESS_THAN_OR_EQUAL: 'LESS_THAN_OR_EQUAL',
  BETWEEN: 'BETWEEN',
  
  // Text operators
  CONTAINS: 'CONTAINS',
  STARTS_WITH: 'STARTS_WITH',
  ENDS_WITH: 'ENDS_WITH',
  REGEX: 'REGEX',
  
  // Boolean operators
  IS_EMPTY: 'IS_EMPTY',
  IS_NOT_EMPTY: 'IS_NOT_EMPTY',
  
  // Logical operators
  AND: 'AND',
  OR: 'OR',
  NOT: 'NOT'
};

/**
 * Evaluate a dependency expression.
 * 
 * @param {object} expression - The dependency expression (JSON structure)
 * @param {object} answersDict - Dictionary mapping question_id to answer value
 * @returns {boolean} True if the condition is satisfied
 */
export function evaluateDependency(expression, answersDict) {
  if (!expression) {
    return true;
  }
  
  const operator = expression.operator;
  
  // Handle logical operators (AND, OR, NOT)
  if ([DependencyOperator.AND, DependencyOperator.OR, DependencyOperator.NOT].includes(operator)) {
    return evaluateLogical(expression, answersDict);
  }
  
  // Handle leaf condition
  return evaluateCondition(expression, answersDict);
}

/**
 * Evaluate logical operators (AND, OR, NOT)
 */
function evaluateLogical(expression, answersDict) {
  const operator = expression.operator;
  const conditions = expression.conditions || [];
  
  if (operator === DependencyOperator.AND) {
    return conditions.every(cond => evaluateDependency(cond, answersDict));
  }
  
  if (operator === DependencyOperator.OR) {
    return conditions.some(cond => evaluateDependency(cond, answersDict));
  }
  
  if (operator === DependencyOperator.NOT) {
    if (conditions.length !== 1) {
      console.warn(`NOT operator expects exactly 1 condition, got ${conditions.length}`);
      return false;
    }
    return !evaluateDependency(conditions[0], answersDict);
  }
  
  return false;
}

/**
 * Evaluate a single condition
 */
function evaluateCondition(expression, answersDict) {
  const questionId = expression.question_id;
  const operator = expression.operator;
  const values = expression.values || [];
  
  if (questionId === undefined || questionId === null || questionId === '') {
    console.warn('Dependency condition missing question_id');
    return false;
  }
  
  // Get the answer value for this question
  const answerValue = answersDict[questionId];
  
  // Handle IS_EMPTY and IS_NOT_EMPTY
  if (operator === DependencyOperator.IS_EMPTY) {
    return !answerValue || (typeof answerValue === 'string' && answerValue.trim() === '');
  }
  
  if (operator === DependencyOperator.IS_NOT_EMPTY) {
    return answerValue && (typeof answerValue !== 'string' || answerValue.trim() !== '');
  }
  
  // If no answer exists, condition fails (except for empty checks above)
  if (answerValue === undefined || answerValue === null) {
    return false;
  }
  
  const answerStr = String(answerValue);
  
  // Comparison operators
  if (operator === DependencyOperator.EQUALS) {
    return values.length > 0 && answerStr === values[0];
  }
  
  if (operator === DependencyOperator.NOT_EQUALS) {
    return values.length > 0 && answerStr !== values[0];
  }
  
  if (operator === DependencyOperator.IN) {
    return values.includes(answerStr);
  }
  
  if (operator === DependencyOperator.NOT_IN) {
    return !values.includes(answerStr);
  }
  
  // Numeric operators
  if ([DependencyOperator.GREATER_THAN, DependencyOperator.LESS_THAN,
       DependencyOperator.GREATER_THAN_OR_EQUAL, DependencyOperator.LESS_THAN_OR_EQUAL].includes(operator)) {
    return evaluateNumeric(operator, answerStr, values);
  }
  
  if (operator === DependencyOperator.BETWEEN) {
    if (values.length !== 2) {
      console.warn(`BETWEEN operator expects 2 values, got ${values.length}`);
      return false;
    }
    try {
      const val = parseFloat(answerStr);
      const min = parseFloat(values[0]);
      const max = parseFloat(values[1]);
      return min <= val && val <= max;
    } catch (e) {
      return false;
    }
  }
  
  // Text operators
  if (operator === DependencyOperator.CONTAINS) {
    return values.length > 0 && answerStr.includes(values[0]);
  }
  
  if (operator === DependencyOperator.STARTS_WITH) {
    return values.length > 0 && answerStr.startsWith(values[0]);
  }
  
  if (operator === DependencyOperator.ENDS_WITH) {
    return values.length > 0 && answerStr.endsWith(values[0]);
  }
  
  if (operator === DependencyOperator.REGEX) {
    if (values.length === 0) return false;
    try {
      return new RegExp(values[0]).test(answerStr);
    } catch (e) {
      console.warn(`Invalid regex pattern in dependency: ${e.message}`);
      return false;
    }
  }
  
  console.warn(`Unknown dependency operator: ${operator}`);
  return false;
}

/**
 * Evaluate numeric comparison operators
 */
function evaluateNumeric(operator, answerValue, values) {
  if (values.length === 0) return false;
  
  try {
    const answerNum = parseFloat(answerValue);
    const compareNum = parseFloat(values[0]);
    
    if (isNaN(answerNum) || isNaN(compareNum)) {
      return false;
    }
    
    switch (operator) {
      case DependencyOperator.GREATER_THAN:
        return answerNum > compareNum;
      case DependencyOperator.LESS_THAN:
        return answerNum < compareNum;
      case DependencyOperator.GREATER_THAN_OR_EQUAL:
        return answerNum >= compareNum;
      case DependencyOperator.LESS_THAN_OR_EQUAL:
        return answerNum <= compareNum;
      default:
        return false;
    }
  } catch (e) {
    return false;
  }
}

/**
 * Build answers dictionary from an array of answers
 * @param {Array} answers - Array of {question_id, value} objects
 * @param {Object} linkedResponse - Optional linked form response with answers
 * @returns {Object} Dictionary mapping question_id to value
 */
export function buildAnswersDict(answers, linkedResponse = null) {
  const dict = {};
  if (!answers) return dict;
  
  answers.forEach(answer => {
    if (answer && answer.question_id !== undefined) {
      dict[answer.question_id] = answer.value;
    }
  });
  
  // Add linked form answers if available
  if (linkedResponse && linkedResponse.answers) {
    linkedResponse.answers.forEach(answer => {
      if (answer && answer.question_id !== undefined) {
        // Prefix with 'linked_' to distinguish from current form questions
        dict[`linked_${answer.question_id}`] = answer.value;
        // Also add without prefix for backward compatibility
        dict[answer.question_id] = answer.value;
      }
    });
  }
  
  return dict;
}

export { DependencyOperator };
