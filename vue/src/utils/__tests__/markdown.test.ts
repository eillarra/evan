import { describe, expect, it } from 'vitest';

import { render } from '../markdown';

describe('markdown render', () => {
  it('converts a heading to an <h1> tag', () => {
    const html = render('# Title') as string;
    expect(html).toContain('<h1');
    expect(html).toContain('Title');
  });

  it('converts a paragraph with emphasis', () => {
    const html = render('hello *world*') as string;
    expect(html).toContain('<em>world</em>');
  });

  it('converts a list to <ul>/<li> tags', () => {
    const html = render('- one\n- two') as string;
    expect(html).toContain('<ul>');
    expect(html).toContain('<li>one</li>');
    expect(html).toContain('<li>two</li>');
  });

  it('converts a code block', () => {
    const html = render('```\nconst x = 1;\n```') as string;
    expect(html).toContain('<code>');
  });
});
