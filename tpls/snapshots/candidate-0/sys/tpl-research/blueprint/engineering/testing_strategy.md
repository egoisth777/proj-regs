# Testing Strategy

This document outlines the testing approach and requirements for the project.

## 1. Test-Driven Development (TDD)
- The SDET (Software Development Engineer in Test) agent must write tests *before* the implementation begins.
- Tests should fail initially, serving as the benchmark for Executor agent success.

## 2. Core Test Types
- **Unit Tests:** For testing isolated functions and logic. coverage target is high.
- **Integration Tests:** For component boundaries and database interactions.
- **E2E Tests:** For crucial user workflows.

## 3. CI/CD Requirements
- Tests must be run on every PR.
- Code coverage gates enforce minimum coverage thresholds.
- PRs cannot be merged without 100% test pass rate.
