# Main evaluation results

These files contain the non-ablation aggregate results used for the main evaluation table.

- `main_results.csv`: one row per benchmark/model/method condition.
- `main_results.json`: the same rows plus schema and provenance metadata.

`ts`, `proper`, `under`, and `over` are percentages. `task_similarity` is the ToolSandbox milestone score multiplied by 100; it is `null` for BFCL. `ster` is successful tasks per 100 external tool calls and `spr` is the percentage of tasks that are both successful and Proper. `n` is the number of scenarios.

The result rows include Prompting, SMARTAgent, MetaAgent, and Aster. No ablation variant, raw trajectory, API response, or private path is included.
