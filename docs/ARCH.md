<!-- ===================================================== -->
<!-- ASSIST_KEY: 【docs/ARCH.md】                          -->
<!-- ===================================================== -->
# mmopdca — Architecture Overview (MVP 2025-05)

```mermaid
graph TD
    subgraph Presentation
        A1[FastAPI / Swagger<br/>api/main_api.py]
        A2[React (予定)]
    end
    subgraph Routers
        R1[/plan<br/>plan_api]
        R2[/plan-dsl<br/>plan_dsl_api]
        R3[/do<br/>do_api]
        R4[/metrics<br/>metrics_api]
        R5[/metrics (export)<br/>metrics_exporter]
    end
    subgraph Core
        C1[loader.py<br/>splitter.py]
        C2[engineering.py]
        C3[trainer.py]
        C4[predictor.py]
        C5[metrics.py]
    end
    subgraph Repository
        S1[metrics_repo.py]
        S2[factory.py]
        S3[Memory / Redis<br/>(future)]
    end
    %% edges
    A1 -->|include_router| R1 & R2 & R3 & R4
    A1 --> R5
    R3 --> C1 & C2 & C3 & C4 & C5
    R4 & R5 --> S1
    C3 & C4 --> S1
    S1 -->|get_repo| S2
