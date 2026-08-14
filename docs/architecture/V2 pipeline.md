# V2 Pipeleine
                
                Scan Request
                     │
                     ▼
             ScanPipeline
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   Create Scan Aggregate    Normalize Source
          │                     │
          └──────────┬──────────┘
                     ▼
              Analyzer Ports
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       Slither    Mythril    Echidna
          │          │          │
          └──────────┴──────────┘
                     ▼
                  Findings
                     │
                     ▼
          FindingCorrelationService
                     │
                     ▼
               AttackPathService
                     │
                     ▼
             RecommendationService
                     │
                     ▼
             RiskAssessmentService
                     │
                     ▼
               Completed Scan