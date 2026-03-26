/**
 * PostToolUse hook: polls GitHub PR for CI checks and reviews.
 * Reads tool use result from stdin, outputs feedback to stdout.
 */
import { execSync } from 'child_process';
const POLL_INTERVAL_MS = 30_000;
const TIMEOUT_MS = 30 * 60_000;
export function parsePrUrl(output) {
    const match = output.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
    if (!match)
        return null;
    return {
        owner: match[1],
        repo: match[2],
        pr_number: parseInt(match[3], 10),
    };
}
export function buildFeedbackReport(input) {
    if (input.timeout) {
        return {
            decision: 'allow',
            feedback: {
                timeout: true,
                summary: 'Polling timed out after 30 minutes. Manual review required.',
            },
        };
    }
    const reviewCount = input.reviews?.length ?? 0;
    const commentCount = input.comments?.length ?? 0;
    const checksStatus = input.checks_passed ? 'passed' : 'FAILED';
    return {
        decision: 'allow',
        feedback: {
            checks_passed: input.checks_passed ?? false,
            reviews: input.reviews ?? [],
            comments: input.comments ?? [],
            summary: `CI checks ${checksStatus}. ${reviewCount} review(s) received. ${commentCount} comment(s) to address.`,
        },
    };
}
function runGh(args) {
    try {
        return execSync(`gh ${args}`, { encoding: 'utf-8', timeout: 15_000 });
    }
    catch {
        return null;
    }
}
async function pollChecks(prNumber) {
    const startTime = Date.now();
    while (Date.now() - startTime < TIMEOUT_MS) {
        const output = runGh(`pr checks ${prNumber} --json name,state,conclusion`);
        if (!output)
            return 'timeout';
        try {
            const checks = JSON.parse(output);
            const hasFailure = checks.some(c => c.conclusion === 'FAILURE');
            if (hasFailure)
                return false;
            const allDone = checks.every(c => c.state === 'COMPLETED');
            if (allDone)
                return true;
        }
        catch {
            // Parse error — continue polling
        }
        await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
    }
    return 'timeout';
}
function fetchReviews(owner, repo, prNumber) {
    const output = runGh(`api repos/${owner}/${repo}/pulls/${prNumber}/reviews`);
    if (!output)
        return [];
    try {
        const data = JSON.parse(output);
        return data.map((r) => ({ state: r.state, user: r.user?.login ?? 'unknown' }));
    }
    catch {
        return [];
    }
}
function fetchComments(owner, repo, prNumber) {
    const output = runGh(`api repos/${owner}/${repo}/pulls/${prNumber}/comments`);
    if (!output)
        return [];
    try {
        const data = JSON.parse(output);
        return data.map((c) => ({ body: c.body ?? '', user: c.user?.login ?? 'unknown' }));
    }
    catch {
        return [];
    }
}
async function main() {
    let inputData;
    try {
        const stdin = await new Promise((resolve) => {
            let data = '';
            process.stdin.on('data', (chunk) => { data += chunk; });
            process.stdin.on('end', () => resolve(data));
        });
        inputData = JSON.parse(stdin);
    }
    catch {
        process.stdout.write(JSON.stringify({ decision: 'allow' }));
        return;
    }
    // Note: field name may vary in Claude Code hook protocol — verify against docs
    const toolOutput = inputData.tool_output ?? inputData.result ?? '';
    const prInfo = parsePrUrl(toolOutput);
    if (!prInfo) {
        process.stdout.write(JSON.stringify({ decision: 'allow' }));
        return;
    }
    const { owner, repo, pr_number } = prInfo;
    const checksResult = await pollChecks(pr_number);
    if (checksResult === 'timeout') {
        const report = buildFeedbackReport({ timeout: true });
        process.stdout.write(JSON.stringify(report));
        return;
    }
    const reviews = fetchReviews(owner, repo, pr_number);
    const comments = fetchComments(owner, repo, pr_number);
    const report = buildFeedbackReport({
        checks_passed: checksResult,
        reviews,
        comments,
    });
    process.stdout.write(JSON.stringify(report));
}
main();
