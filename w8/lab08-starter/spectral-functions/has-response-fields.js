module.exports = (schema, _options, context) => {
  if (!schema || typeof schema !== 'object') {
    return [{
      message: 'Response schema must be an object.'
    }];
  }

  const document = context.document.data;

  function resolveRef(ref) {
    if (!ref || !ref.startsWith('#/')) return null;

    return ref
      .slice(2)
      .split('/')
      .map(part => part.replace(/~1/g, '/').replace(/~0/g, '~'))
      .reduce((obj, key) => obj?.[key], document);
  }

  function hasFields(current, visited = new Set()) {
    if (!current || typeof current !== 'object') return false;

    if (current.$ref) {
      if (visited.has(current.$ref)) return false;
      visited.add(current.$ref);

      return hasFields(resolveRef(current.$ref), visited);
    }

    if (current.type === 'array') {
      return hasFields(current.items, visited);
    }

    if (current.type === 'object') {
      return Object.keys(current.properties || {}).length > 0;
    }

    return Object.keys(current.properties || {}).length > 0;
  }

  if (hasFields(schema)) {
    return;
  }

  return [{
    message: 'A 200 response schema must contain at least one field.'
  }];
};