# Architect's Note #36 – Value Objects Should Be Small but Complete

One of the characteristics of a mature domain model is that Value Objects tend to become smaller as the architecture evolves. As responsibilities are separated into dedicated services and derived artifacts become independent concepts, the Value Object is left with only its essential facts and intrinsic behavior.

CodeContext is a good example of this evolution. It stores only the canonical semantic facts that define the context of a vulnerability and delegates normalization, fingerprinting, and analysis to specialized domain services. This results in a class that is simple to understand, impossible to place in an invalid state after construction, and flexible enough to support future enhancements without changing its core responsibility.

I consider this file complete and production-ready. It establishes an excellent foundation for the next component, NormalizedCode, which will naturally consume the output of the forthcoming CodeNormalizer service.