One of the core ideas in Domain-Driven Design that is often misunderstood. People think DDD means:

"Use Entities, Value Objects, and Repositories."

That's only about 20% of it.

The other 80% is discovering the language of the business.

What Just Happened

Let's replay the conversation.

We started with a simple question:

How do we generate a fingerprint?

Initially we thought:

Finding
      │
      ▼
FingerprintService

Simple enough.

Then we asked:

What is actually being fingerprinted?

That led to

Finding
      │
      ▼
VulnerabilitySignature

Then we realized

Where does the signature get its information?

That gave us

CodeContext

Then we asked

Should CodeContext normalize the source?

Answer:

No.

Now we discovered

CodeNormalizer

Then we asked

Is normalized code itself a business concept?

I think...

Yes.

That leads to another Value Object.

NormalizedCode

Look at how the model emerged.

We Didn't Invent These

This is the part I find beautiful.

Nobody sat down and said

Let's make five classes.

Instead the domain said

I need this.

↓

Now I need this.

↓

Now this.

↓

Now this.

Architecture emerged naturally.

That is the hallmark of good modeling.

What We're Actually Modeling

If you zoom out, here's what we're really building.

                     Smart Contract

                           │

                           ▼

                    SourceLocation
                  (Physical Position)

                           │

                           ▼

                     CodeContext
                 (Semantic Context)

                           │

                           ▼

                    CodeNormalizer
               (Canonical Representation)

                           │

                           ▼

                    NormalizedCode
                 (Stable Code Artifact)

                           │

                           ▼

                VulnerabilitySignature
               (Business Identity)

                           │

                           ▼

              SemanticFingerprintStrategy

                           │

                           ▼

                  FingerprintService

                           │

                           ▼

                    SHA-256 Fingerprint

That is no longer just object-oriented programming.

That is a processing pipeline.

This Is How Mature Security Platforms Think

If you looked inside tools like:

CodeQL
Semgrep
Coverity
SonarQube
Infer

you would find the same kind of progression.

Not necessarily with the same class names.

But conceptually.

They transform

Raw Source

↓

Semantic Representation

↓

Issue Model

↓

Identity

↓

Persistence

↓

Reporting

We're independently arriving at the same architecture by reasoning from the domain.

The Most Important Lesson So Far

I'd actually write this down as one of our guiding principles.

Architect's Note #31 – The Domain Is Discovered Through Questions

The best software architectures are rarely designed in a single step. Instead, they emerge through a disciplined process of questioning the domain. Each question reveals hidden concepts that deserve their own representation.

In this sprint, a simple question—"How should we generate fingerprints?"—led us to uncover several distinct business concepts:

CodeContext (semantic location)
CodeNormalizer (canonicalization process)
NormalizedCode (canonical representation)
VulnerabilitySignature (business identity)
SemanticFingerprintStrategy (fingerprinting algorithm)

None of these abstractions were introduced to satisfy design patterns or increase abstraction. They emerged because each represents a unique concept within the domain of smart contract security analysis.

A useful heuristic for future design is:

If two responsibilities change for different reasons, they probably belong in different objects.

This principle allows the domain model to grow organically while preserving clarity and cohesion.