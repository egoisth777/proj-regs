/**
 * PostToolUse hook: polls GitHub PR for CI checks and reviews.
 * Reads tool use result from stdin, outputs feedback to stdout.
 */
export interface PrInfo {
    owner: string;
    repo: string;
    pr_number: number;
}
export interface FeedbackInput {
    checks_passed?: boolean;
    reviews?: Array<{
        state: string;
        user: string;
    }>;
    comments?: Array<{
        body: string;
        user: string;
    }>;
    timeout?: boolean;
}
export interface PostPrWaitResult {
    decision: string;
    feedback: {
        checks_passed?: boolean;
        reviews?: Array<{
            state: string;
            user: string;
        }>;
        comments?: Array<{
            body: string;
            user: string;
        }>;
        timeout?: boolean;
        summary: string;
    };
}
export declare function parsePrUrl(output: string): PrInfo | null;
export declare function buildFeedbackReport(input: FeedbackInput): PostPrWaitResult;
