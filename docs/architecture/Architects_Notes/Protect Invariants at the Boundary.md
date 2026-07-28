Architect's Note #20 – Protect Invariants at the Boundary

An entity's constructor is its first and most important line of defence.

If invalid state is allowed during construction, every other method in the entity must continually defend against bad data. That leads to defensive programming, duplicated checks, and fragile code.

By enforcing invariants inside __post_init__(), we guarantee that every Finding instance is valid from the moment it exists. This simplifies the rest of the codebase because methods can safely assume the entity's state is already correct.

This approach aligns with Domain-Driven Design: entities should protect their own consistency, rather than relying on callers to behave correctly.

After this commit, our Finding entity will no longer be just a container for data—it will actively enforce the rules of the scanning domain. The next sprint will focus on adding domain behaviors (summary(), is_critical, requires_attention, matches()), which will make the entity expressive and behavior-rich rather than an anemic model.