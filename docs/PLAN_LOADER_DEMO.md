<!-- ========================================================= -->
<!-- ASSIST_KEY: 【docs/PLAN_LOADER_DEMO.md】                   -->
<!-- ========================================================= -->
# Plan DSL Loader Demo

This short example shows how to load a DSL file using `PlanLoader` with the
built-in model schema. The loader automatically applies default values from
`core/dsl/schemas/models_schema.json` and validates the structure.

```python
from core.dsl.loader import PlanLoader

loader = PlanLoader(validate=True)
plan = loader.load("docs/samples/plan_sample.yaml")
print(plan["models"])
```

Running the above will print the merged configuration with defaults inserted.