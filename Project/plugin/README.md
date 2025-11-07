# huycnv

`huycnv` provides shared data models and an abstract plugin base class for CNV algorithm integrations.

## Installation

```bash
pip install huycnv
```

## Usage

```python
from huycnv.plugin import AlgorithmPlugin, BaseInput, BaseOutput
```

Define a custom plugin by subclassing `AlgorithmPlugin` and implementing the `run` method.
