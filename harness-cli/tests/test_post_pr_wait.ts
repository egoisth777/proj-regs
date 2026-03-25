import { describe, it, expect } from 'vitest';
import { parsePrUrl, buildFeedbackReport } from '../hooks/post_pr_wait.js';

describe('parsePrUrl', () => {
  it('extracts owner, repo, and PR number from URL', () => {
    const result = parsePrUrl('https://github.com/acme/myrepo/pull/42');
    expect(result).toEqual({ owner: 'acme', repo: 'myrepo', pr_number: 42 });
  });

  it('handles URL with trailing newline', () => {
    const result = parsePrUrl('https://github.com/acme/myrepo/pull/42\n');
    expect(result).toEqual({ owner: 'acme', repo: 'myrepo', pr_number: 42 });
  });

  it('returns null for non-PR output', () => {
    const result = parsePrUrl('Created branch feat/auth');
    expect(result).toBeNull();
  });

  it('returns null for empty string', () => {
    const result = parsePrUrl('');
    expect(result).toBeNull();
  });

  it('extracts from multi-line output', () => {
    const output = 'Creating pull request...\nhttps://github.com/acme/repo/pull/99\n';
    const result = parsePrUrl(output);
    expect(result).toEqual({ owner: 'acme', repo: 'repo', pr_number: 99 });
  });
});

describe('buildFeedbackReport', () => {
  it('builds success report', () => {
    const result = buildFeedbackReport({
      checks_passed: true,
      reviews: [{ state: 'APPROVED', user: 'bot' }],
      comments: [{ body: 'LGTM', user: 'reviewer' }],
    });
    expect(result.decision).toBe('allow');
    expect(result.feedback.checks_passed).toBe(true);
    expect(result.feedback.summary).toContain('1 review');
    expect(result.feedback.summary).toContain('1 comment');
  });

  it('builds failure report', () => {
    const result = buildFeedbackReport({
      checks_passed: false,
      reviews: [],
      comments: [],
    });
    expect(result.decision).toBe('allow');
    expect(result.feedback.checks_passed).toBe(false);
    expect(result.feedback.summary).toContain('FAILED');
  });

  it('builds timeout report', () => {
    const result = buildFeedbackReport({ timeout: true });
    expect(result.decision).toBe('allow');
    expect(result.feedback.timeout).toBe(true);
    expect(result.feedback.summary).toContain('timed out');
  });
});
