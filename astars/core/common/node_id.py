class UnstableNodeID:
    _counter = 0

    @classmethod
    def new(cls) -> int:
        cls._counter += 1
        return cls._counter
