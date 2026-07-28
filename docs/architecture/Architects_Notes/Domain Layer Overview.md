Architect's Notes #1
Purpose

The Domain Layer represents the business knowledge of FinSec Guardian.

It answers questions like:

What is a security finding?
What is a scan?
What is a risk?
What rules must always be true?

It should not know anything about:

Django
PostgreSQL
REST APIs
JSON
Celery
HTTP
ORM models

Those belong elsewhere.

Mental Model
                   DOMAIN
────────────────────────────────────

        "What does the business know?"

            Entities
               ▲
               │
        Value Objects
               ▲
               │
             Enums
               ▲
               │
          Exceptions

The domain is the heart of the application. Everything else exists to support it.

Owns
Business rules
Validation
Domain behaviour
Ubiquitous language
Business concepts
Does NOT Own
Database tables
Serializers
API Views
Django Models
HTTP Requests
Collaborates With
Application Layer

↓

Infrastructure

↓

Presentation

The Domain never depends on them.