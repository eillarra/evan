/**
 * Convert tags array to dictionary
 * @param tags - tags array
 * @returns tags dictionary
 * @example
 * tags_to_dict(['tag1:value1', 'tag2:value2', tag3:"hour:min"])
 * // => { tag1: 'value1', tag2: 'value2', tag3: 'hour:min' }
 */
function tags_to_dict(tags: Tags): TagsDict {
  return tags.reduce((dict, tag) => {
    const parts = tag.split(':');
    const value = parts.slice(1).join(':');
    dict[parts[0]] = value.replace(/^"|"$/g, '');
    return dict;
  }, {} as TagsDict);
}

export { tags_to_dict };
