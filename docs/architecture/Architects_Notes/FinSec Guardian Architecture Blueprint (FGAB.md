# FinSec Guardian Architecture Blueprint (FGAB)
                   
                   FINSEC GUARDIAN
                 Architecture Blueprint

 ┌──────────────────────────────────────────────────────────┐
 │                 1. DOMAIN MODEL                          │
 └──────────────────────────────────────────────────────────┘

      Entities
      Value Objects
      Enums
      Domain Services
      Domain Events
      Exceptions

                ↓

 ┌──────────────────────────────────────────────────────────┐
 │              2. APPLICATION LAYER                        │
 └──────────────────────────────────────────────────────────┘

      Use Cases
      DTOs
      Commands
      Queries
      Validators

                ↓

 ┌──────────────────────────────────────────────────────────┐
 │            3. INFRASTRUCTURE LAYER                       │
 └──────────────────────────────────────────────────────────┘

      Django ORM
      Repositories
      Mappers
      Slither Adapter
      Mythril Adapter
      Echidna Adapter
      AI Adapter

                ↓

 ┌──────────────────────────────────────────────────────────┐
 │             4. PRESENTATION LAYER                        │
 └──────────────────────────────────────────────────────────┘

      REST API
      Authentication
      WebSockets
      CLI

                ↓

 ┌──────────────────────────────────────────────────────────┐
 │              5. SCANNING PIPELINE                        │
 └──────────────────────────────────────────────────────────┘

      Upload
          ↓
      Compile
          ↓
      Analyze
          ↓
      Normalize
          ↓
      Risk Score
          ↓
      Persist
          ↓
      Report

                ↓

 ┌──────────────────────────────────────────────────────────┐
 │              6. REPORTING ENGINE                         │
 └──────────────────────────────────────────────────────────┘

      HTML
      PDF
      JSON
      SARIF
      Executive Report