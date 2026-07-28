# Architect's Note #27 – Discover the Model, Don't Force It

A common mistake in software design is to begin by choosing patterns ("We'll use Strategy," "We'll use Factory") before understanding the domain. This often results in unnecessary abstractions.

In FinSec Guardian, we are taking the opposite approach. We first identify the business concepts—such as CodeContext and VulnerabilitySignature—and only introduce architectural patterns when the domain demonstrates a genuine need. The Strategy pattern emerges naturally because fingerprint generation has multiple legitimate algorithms, not because we wanted to use a design pattern.

This is a key principle of Domain-Driven Design: let the domain shape the architecture, rather than forcing the architecture onto the domain.